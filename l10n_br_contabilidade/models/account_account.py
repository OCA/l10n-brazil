# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import _, api, fields, models


class AccountAccount(models.Model):
    _inherit = 'account.account'

    natureza_conta_id = fields.Many2one(
        string='Natureza da Conta',
        comodel_name='account.natureza',
    )

    saldo = fields.Float(
        string='Saldo',
        compute='_compute_saldo_conta',
    )

    identificacao_saldo = fields.Selection(
        string='Identificação de Saldo',
        selection=[
            ('', ''),
            ('debito', 'D'),
            ('credito', 'C'),
        ],
        default='debito',
        compute='_get_identificacao_saldo',
    )

    funcao = fields.Text(
        string=u'Função',
    )

    funcionamento = fields.Text(
        string=u'Funcionamento',
    )

    observacao = fields.Text(
        string=u'Observação',
    )

    precisa_ramo = fields.Boolean(
        string=u'É obrigatório definir Ramo?'
    )

    depara_ids = fields.One2many(
        string=u'Mapeamento DePara',
        comodel_name='account.mapeamento',
        inverse_name='conta_sistema_id',
    )

    divisao_resultado_ids = fields.One2many(
        string=u'Fechamentos vinculados',
        comodel_name='account.divisao.resultado',
        inverse_name='account_id',
    )

    account_account_report_id = fields.Many2many(
        string=u'Estrutura de Apresentação',
        comodel_name='account.account.report',
        relation='account_account_account_report_rel',
        column1='account_report_id',
        column2='account_account_id',
        domain = "[('type','=',tipo_conta_apresentacao)]",
    )

    report_type = fields.Selection(
        related='user_type.report_type',
        selection=[
            ('none', '/'),
            ('income', _('Profit & Loss (Income account)')),
            ('expense', _('Profit & Loss (Expense account)')),
            ('asset', _('Balance Sheet (Asset account)')),
            ('liability', _('Balance Sheet (Liability account)'))
        ],
        help="This field is used to generate legal reports: "
             "profit and loss, balance sheet.",
        required=True
    )

    tipo_conta_apresentacao = fields.Char(
        string='Tipo Conta Apresentacao',
        help=u'Indicar se a conta de apresentacao e do tipo patrimonial ou '
             u'de resultado',
        compute='compute_tipo_apresentacao',
    )

    @api.multi
    @api.depends('report_type')
    def compute_tipo_apresentacao(self):
        """
        :return:
        """
        for record in self:
            if record.report_type in ['income','expense']:
                record.tipo_conta_apresentacao = 'resultado'
            elif record.report_type in ['asset','liability']:
                record.tipo_conta_apresentacao = 'patrimonial'
            else:
                record.tipo_conta_apresentacao = ''

    @api.depends('balance')
    def _compute_saldo_conta(self):
        """
        Utilizar a natureza da conta para manipular o valor de saldo
        calculado automáticamente pela funcionalidade do core.

        obs: Este campo está subistituindo o cambo 'balance' do core na visão
        """
        for record in self:
            saldo = record.balance
            if saldo < 0:
                saldo *= -1

            record.saldo = saldo

    @api.depends('saldo')
    def _get_identificacao_saldo(self):
        for record in self:
            if record.debit > record.credit:
                record.identificacao_saldo = 'debito'
            elif record.debit < record.credit:
                record.identificacao_saldo = 'credito'
            else:
                record.identificacao_saldo = ''

    @api.v7
    def _check_allow_code_change(self, cr, uid, ids, context=None):
        """
        :return:
        """
        if not self.user_has_groups(cr, uid, 'base.group_no_one'):
            return super(AccountAccount, self)._check_allow_code_change(
                cr, uid, ids, context=context)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        def ignora_ponto(res):
            request = "SELECT id, concat_ws(' ', code, name) " \
                      "FROM account_account " \
                      "WHERE " \
                      "REPLACE(code, '.', '') LIKE " \
                      "REPLACE('{}%', '.', '')".format(name)

            self.env.cr.execute(request)

            for row in self.env.cr.fetchall():
                res.append(row)

            return res

        res = super(AccountAccount, self).name_search(name)
        if not res:
            domain_name = '%{}%'.format(name)
            res = self.search([('code', '=ilike', domain_name)])
            res = res.name_get()
            res = ignora_ponto(res)

            return res

        res = ignora_ponto(res)

        return res
