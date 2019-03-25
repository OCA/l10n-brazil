# -*- coding: utf-8 -*-
# Copyright 2019 ABGF.gov.br Luciano Veras
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime
from time import gmtime, strftime
from openerp import api, fields, models, _


class ContractRessarcimentoConfig(models.Model):
    _name = b'contract.ressarcimento.config'
    _description = u'Configurações do Ressarcimento de Contrato'

    contract_ressarcimento_config_line_ids = fields.One2many(
        inverse_name='contract_ressarcimento_config_id',
        comodel_name='contract.ressarcimento.config.line',
        string=u'Ressarcimento do Contrato',
    )

    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='contract_ressarcimento_config_rel',
        column1='contract_ressarcimento_config_id',
        column2='partner_id',
        string=u'Parceiros para alertar no dia limite',
        help=u'Parceiros que receberão alertas caso não exista registro '
             u'de ressarcimento/provisão para o contrato.'
    )

    nt_st_partner_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='contract_ressarcimento_rel',
        column1='contract_ressarcimento_config_id',
        column2='partner_id',
        string=u'Parceiros para notificar mudança de status',
        help=u'Parceiros que receberão alertas da mudança de status do'
             u'do ressarcimento.'
    )

    dias_apos_provisao = fields.Integer(
        string=u'Dias após provisão',
        help=u'Quantidade de dias que o sistema deve alertar caso haja '
             u'valor provisionado, mas sem o ressarcimento real, contados '
             u'a partir do dia limite para inclusão definido no item '
             u'acima.',
    )

    @api.multi
    def salvar_config(self):
        self.exclui_contratos_expirados()

    @api.multi
    def exclui_contratos_expirados(self):
        '''
        Verifica se existe contratos expirados e exclui para que não exista
        mais notificações para o contrato.

        :return:
        '''
        self.ensure_one()

        self.contract_ressarcimento_config_line_ids.filtered(
            lambda x: x.contract_id.date_end is not False).unlink()

    @api.multi
    def contrato_dia_limite_hoje(self, ap_prov=False):
        '''
        Busca contratos fora do prazo com base na data atual e o dia
        estabelecido no parâmetro.

        :param ap_prov:
        :return:
        '''
        self.ensure_one()

        hoje = int(strftime("%d", gmtime()))
        dias_ap_prov = self.dias_apos_provisao if ap_prov else 0
        c_hoje = self.contract_ressarcimento_config_line_ids.\
            filtered(lambda x: x.dia_limite+dias_ap_prov <= hoje)

        return c_hoje

    @api.multi
    def busca_fora_prazo(self, competencia, ap_prov=False):
        for record in self:
            # Contratos com a mesma data de hoje
            c_hoje = record.contrato_dia_limite_hoje(ap_prov=ap_prov)

            c_fora_prazo = []

            # Verifica se existe registro de contrato para ressarcimento
            if len(c_hoje) > 0:

                # Complementa o domain para buscar contratos com provisão
                # sem data de ressarcimento definida
                comp = ('date_ressarcimento', '!=', False) \
                    if ap_prov else (True, '=', True)

                # Busca id dos contratos sem Ressarcimento na data limite
                contract_ids = c_hoje.mapped('contract_id').mapped('id')

                contract_res_ids = self.env['contract.ressarcimento'].\
                    search([('contract_id', 'in', contract_ids),
                            ('account_period_id.name', '=', competencia),
                            comp]).mapped('contract_id').mapped('id')

                # IDs dos contratos sem ressarcimento cadastrados fora do prazo
                c_fora_prazo = list(set(contract_ids) - set(contract_res_ids))

            return c_fora_prazo

    @api.model
    def notifica_fora_prazo(self, ap_prov=False, notificados=[]):
        '''
        Este metodo é chamado pelo cron do odoo ir.cron
        (hr_contract_ressarcimento_config_cron)
        Notifica ressarcimentos fora do prazo de cadastro

        ap_prov: após provisionamento
        notificados: notificados na primeira interação
        :return:
        '''
        # força self buscar o primeiro registro
        self = self.browse(1)

        # Exclui da lista contratos expirados
        self.exclui_contratos_expirados()

        # pega mês/ano anterior
        hoje = datetime.date.today()
        primeiro = hoje.replace(day=1)
        ultimo_mes = primeiro - datetime.timedelta(days=1)
        competencia = ultimo_mes.strftime("%m/%Y")

        c_fora_prazo = self.busca_fora_prazo(competencia=competencia,
                                             ap_prov=ap_prov)

        c_fora_prazo = list(set(c_fora_prazo) - set(notificados))

        if len(c_fora_prazo) > 0:
            fora_prazo = self.contract_ressarcimento_config_line_ids.filtered(
                lambda x: x.contract_id.id in c_fora_prazo)
            partner_ids = self.partner_ids

            for line in fora_prazo:
                line.send_mail(partner_ids=partner_ids,
                               competencia=competencia, ap_prov=ap_prov)

        # Repete o procedimento com ap_prov=True
        if ap_prov is False:
            self.notifica_fora_prazo(ap_prov=True, notificados=c_fora_prazo)


class ContractRessarcimentoConfigLine(models.Model):
    _name = b'contract.ressarcimento.config.line'
    _inherit = ['mail.thread']
    _sql_constraints = [
        ('contract_id_config_line_unique',
         'unique (contract_id, contract_ressarcimento_config_id)',
         'Já existe alerta configurado para esse contrato')]

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
    def send_mail(self, partner_ids, competencia, ap_prov=False):
        """
        Envia emails quando fora do prazo definido
        """
        mail_obj = self.env['mail.mail']
        val = self.prepara_mail(partner_ids=partner_ids,
                                competencia=competencia, ap_prov=ap_prov)
        mail_id = mail_obj.create(val)
        mail_obj.send(mail_id)

    def prepara_mail(self, partner_ids, competencia, ap_prov=False):
        template_name = 'l10n_br_ressarcimento.' \
            'email_template_contract_ressarcimento_alert'

        template_name = template_name + 'p' if ap_prov else template_name

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
