# -*- coding: utf-8 -*-
# Copyright 2018 ABGF.gov.br Hendrix Costa
# Copyright 2019 ABGF.gov.br Luciano Veras
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import unicode_literals, division, absolute_import, print_function


from openerp import api, fields, models, _


class ContractRessarcimento(models.Model):
    _name = b'contract.ressarcimento'
    _inherit = ['mail.thread']
    _description = 'Ressarcimentos de outros Vínculos do Contrato'
    _order = "account_period_id DESC"

    name = fields.Char(
        string='Nome',
    )

    state = fields.Selection(
        selection=[
            ('aberto', 'Aberto'),
            ('confirmado', 'Aguardando aprovação'),
            ('provisionado', 'Provisionado'),
            ('aprovado', 'Aprovado'),
        ],
        string='Situação',
        default='aberto',
    )

    date_ressarcimento = fields.Date(
         string='Data do Ressarcimento',
    )

    date_provisao = fields.Date(
         string='Data da Provisão',
    )

    contract_id = fields.Many2one(
        comodel_name="hr.contract",
        string="Contrato",
        default=lambda self: self.env.context.get('default_contract_id'),
    )

    default_contract_id = fields.Boolean(
        string="Contrato",
        default=lambda self: 1 if self.env.context.get('default_contract_id')
        else 0,
    )

    contract_ressarcimento_line_ids = fields.One2many(
        inverse_name='contract_ressarcimento_id',
        comodel_name='contract.ressarcimento.line',
        string='Ressarcimento do Contrato',
    )

    contract_ressarcimento_provisionado_line_ids = fields.One2many(
        inverse_name='contract_ressarcimento_provisionado_id',
        comodel_name='contract.ressarcimento.line',
        string='Ressarcimento do Contratro (provisionado)',
    )

    account_period_id = fields.Many2one(
        comodel_name='account.period',
        string='Competência',
        domain="[('special', '=', False), ('state', '=', 'draft')]",
    )

    total_provisionado = fields.Float(
        string=u"Total de Ressarcimento Provisionado",
        compute='compute_total_ressarcimento',
        store=True,
    )

    total = fields.Float(
        string=u"Total de Ressarcimento",
        compute='compute_total_ressarcimento',
        store=True,
    )

    valor_provisionado = fields.Boolean(
        string='Valor Provisionado?',
    )

    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Parceiros para notificar',
    )

    enviado_por = fields.Many2one(
        string='Enviado por',
        comodel_name='res.users',
    )

    aprovado_por = fields.Many2one(
        string='Aprovado por',
        comodel_name='res.users',
    )

    provisao_aprovado_por = fields.Many2one(
        string='Aprovado por (provisão)',
        comodel_name='res.users',
    )

    provisao_enviado_por = fields.Many2one(
        string='Enviado por (provisão)',
        comodel_name='res.users',
    )

    @api.model
    def create(self, vals):
        # name = "nome contrato" - "competencia"
        vals['name'] = '{} - {}'.format(
            self.contract_id.browse(vals.get('contract_id')).name,
            self.account_period_id.browse(
                vals.get('account_period_id')).name)

        return super(ContractRessarcimento, self).create(vals)

    @api.onchange('valor_provisionado')
    def onchange_valor_provisionado(self):
        """
        Caso estado aberto, se for um valor provisionado,
        precisa que delete informações colocadas referente a
        competencia e valores não provisionados
        :return:
        """
        if self.state == 'aberto':
            if self.valor_provisionado:
                self.date_ressarcimento = False
                self.contract_ressarcimento_line_ids = False
            else:
                self.date_provisao = False
                self.contract_ressarcimento_provisionado_line_ids = False

    @api.multi
    @api.depends('contract_ressarcimento_line_ids')
    def compute_total_ressarcimento(self):
        # somatorio das rubricas de ressarcimento e provisão, separadamente.
        for record in self:
            record.total = sum(
                record.contract_ressarcimento_line_ids.mapped('total'))

            record.total_provisionado = sum(
                record.contract_ressarcimento_provisionado_line_ids.mapped(
                    'total'))

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = 'Ressarcimento {} [{}]'.format(
                record.contract_id.employee_id.name,
                record.account_period_id.name
            )
            result.append((record['id'], name))
        return result

    @api.multi
    def button_confirm(self):
        """
        Operador confirmando e submetendo para aprovação
        """
        for record in self:
            record.send_mail(situacao='confirmado')
            if record.state == 'aberto':
                if record.valor_provisionado and not record.date_ressarcimento:
                    record.provisao_enviado_por = self.env.user.id
                else:
                    record.enviado_por = self.env.user.id

            elif record.state == 'provisionado':
                record.enviado_por = self.env.user.id

            record.state = 'confirmado'

    @api.multi
    def button_aprovar(self):
        """
        Aprovação
        """
        for record in self:
            # Valor provisionado TRUE e não definido data do ressarcimento
            # A aprovação é para a provisão, se não aprova o ressarcimento
            if record.valor_provisionado and not record.date_ressarcimento:
                record.provisao_aprovado_por = self.env.user.id
                record.state = 'provisionado'
            else:
                record.aprovado_por = self.env.user.id
                record.state = 'aprovado'

            record.send_mail(situacao='aprovado')

    @api.multi
    def button_reprovar(self):
        """
        Reporvar
        """
        for record in self:
            if record.valor_provisionado is False\
                    or (record.valor_provisionado
                        and not record.date_ressarcimento):
                record.state = 'aberto'
                record.aprovado_por = False
                record.enviado_por = False
                record.provisao_aprovado_por = False
                record.provisao_enviado_por = False
            elif record.valor_provisionado and record.date_ressarcimento:
                record.state = 'provisionado'
                record.aprovado_por = False
                record.enviado_por = False

            record.send_mail(situacao='reprovado')

    @api.multi
    def button_send_mail(self):
        """
        """
        for record in self:
            record.send_mail(situacao=record.state)

    def prepara_mail(self, situacao='aprovado'):
        template_name = \
            'l10n_br_ressarcimento.' \
            'email_template_contract_ressarcimento_{}'.format(situacao)

        # template para valor provisionado
        if self.valor_provisionado and not self.date_ressarcimento:
            template_name = template_name + 'p'

        template = self.env.ref(template_name, False)
        for record in self:
            # gera template
            vals = template.generate_email_batch(template.id, [record.id])
            val = vals[record.id]

            # Adiciona os partners a serem reportados
            emails = record.partner_ids.filtered('email').mapped('email')
            email_to = ','.join(emails)
            partner_ids = record.partner_ids.mapped('id')
            val.update(partner_ids=partner_ids)
            val.update(email_to=email_to)

        return val

    @api.multi
    def send_mail(self, situacao='aprovado'):
        """
        Email serão mandados em 2 momentos:
        Confirmação: após criação um ressarcimento deverá ser submetido
                    à aprovação
        Aprovação: Email para avisar da pendencia de um ressarcimento aprovação
        """
        mail_obj = self.env['mail.mail']
        val = self.prepara_mail(situacao=situacao)
        mail_id = mail_obj.create(val)
        mail_obj.send(mail_id)


class ContractRessarcimentoLine(models.Model):
    _name = b'contract.ressarcimento.line'
    _description = 'Linhas dos Ressarcimentos de outros Vínculos'
    _order = 'descricao'

    name = fields.Char(
        string='Name',
    )

    contract_ressarcimento_id = fields.Many2one(
        comodel_name='contract.ressarcimento',
        string='Ressarcimento do Contratro',
    )

    contract_ressarcimento_provisionado_id = fields.Many2one(
        comodel_name='contract.ressarcimento',
        string='Ressarcimento do Contratro',
    )

    descricao = fields.Char(
        string="Rubricas de Ressarcimento",
    )

    total = fields.Float(
        string=u"Valor",
    )

    @api.model
    def create(self, vals):
        vals['name'] = '{} - {}'.format(
            self.contract_ressarcimento_id.browse(
                vals.get('contract_ressarcimento_id')).name or
            self.contract_ressarcimento_provisionado_id.browse(
                vals.get('contract_ressarcimento_provisionado_id')).name,
            vals.get('descricao'))

        return super(ContractRessarcimentoLine, self).create(vals)
