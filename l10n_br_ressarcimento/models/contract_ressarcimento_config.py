# -*- coding: utf-8 -*-
# Copyright 2019 ABGF.gov.br Luciano Veras
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from time import gmtime, strftime
from openerp import api, fields, models, _


class ContractRessarcimentoConfig(models.Model):
    _name = b'contract.ressarcimento.config'
    _description = u'Configurações do Ressarcimento de Contrato'

    contract_ressarcimento_config_line_ids = fields.One2many(
        inverse_name='contract_ressarcimento_config_id',
        comodel_name='contract.ressarcimento.config.line',
        string='Ressarcimento do Contrato',
    )

    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Parceiros para notificar',
    )

    @api.multi
    def salvar_config(self):
        pass

    def busca_fora_prazo(self):
        hoje = int(strftime("%d", gmtime()))
        competencia = strftime("%m/%Y", gmtime())

        # Contratos com a mesma data de hoje
        c_hoje = self.contract_ressarcimento_config_line_ids.\
            filtered(lambda x: x.dia_limite == hoje)
        c_fora_prazo = []

        # Verifica se existe registro de contrato para ressarcimento
        if len(c_hoje) > 0:
            # Busca contratos sem Ressarcimento para a competência atual
            contract_ids = c_hoje.mapped('contract_id').mapped('id')
            contract_res_ids = self.env['contract.ressarcimento'] \
                .search([('contract_id', 'in', contract_ids),
                         ('account_period_id.name', '=', competencia)]) \
                .mapped('contract_id').mapped('id')

            # IDs dos contratos sem ressarcimento cadastrados fora do prazo
            c_fora_prazo = list(set(contract_ids) - set(contract_res_ids))

        return c_fora_prazo, competencia

    @api.model
    def notifica_fora_prazo(self):
        '''
        Este metodo é chamado pelo cron do odoo
        (hr_contract_ressarcimento_config_cron)
        Notifica ressarcimentos fora do prazo de cadastro
        :return:
        '''
        c_fora_prazo, competencia = self.busca_fora_prazo()
        if len(c_fora_prazo) > 0:
            fora_prazo = self.contract_ressarcimento_config_line_ids.filtered(
                lambda x: x.contract_id.id in c_fora_prazo)
            partner_ids = self.partner_ids

            if len(fora_prazo) > 0:
                for line in fora_prazo:
                    line.send_mail(partner_ids=partner_ids,
                                   competencia=competencia)


class ContractRessarcimentoConfigLine(models.Model):
    _name = b'contract.ressarcimento.config.line'
    _inherit = ['mail.thread']

    contract_ressarcimento_config_id = fields.Many2one(
        comodel_name='contract.ressarcimento.config',
        string='Configuração Ressarcimento',
    )

    contract_id = fields.Many2one(
        comodel_name="hr.contract",
        string="Contrato",
    )

    dia_limite = fields.Integer(
        string='Dia limite',
        default=10,
    )

    account_period = fields.Char()

    @api.multi
    def send_mail(self, partner_ids, competencia):
        """
        Envia emails quando fora do prazo definido
        """
        mail_obj = self.env['mail.mail']
        val = self.prepara_mail(partner_ids=partner_ids,
                                competencia=competencia)
        mail_id = mail_obj.create(val)
        mail_obj.send(mail_id)

    def prepara_mail(self, partner_ids, competencia):
        template_name = \
            'l10n_br_ressarcimento.email_template_contract_ressarcimento_alert'

        template = self.env.ref(template_name, False)
        for record in self:
            record.account_period = competencia

            # gera template
            vals = template.generate_email_batch(template.id,
                                                 [record.id])
            val = vals[record.id]

            # Adiciona os partners e emails a serem reportados
            emails = partner_ids.filtered('email').mapped(
                'email')
            email_to = ','.join(emails)
            val.update(partner_ids=partner_ids.mapped('id'))
            val.update(email_to=email_to)

        return val
