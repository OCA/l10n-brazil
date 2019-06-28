# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import _, api, fields, models
from openerp.exceptions import Warning


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
        compute='_compute_saldo_conta',
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

    parent_id = fields.Many2one(
        comodel_name='account.account',
        domain="[('type', '=', 'view'),"
               "('account_depara_plano_id','=',account_depara_plano_id)]",
    )

    depara_ids = fields.Many2many(
        string=u'DePara de Contas',
        comodel_name='account.depara',
        relation='account_depara_conta_sistema_rel',
        column1='conta_sistema_id',
        column2='account_depara_id',
    )

    reverse_depara_ids = fields.One2many(
        string=u'DePara conta Externa',
        comodel_name='account.depara',
        inverse_name='conta_referencia_id',
    )

    divisao_resultado_ids = fields.One2many(
        string=u'Fechamentos vinculados',
        comodel_name='account.divisao.resultado',
        inverse_name='account_id',
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

    mis_report_kpi_ids = fields.Many2many(
        comodel_name='mis.report.kpi',
        inverse_name='account_ids',
        readonly=True,
    )

    account_depara_plano_id = fields.Many2one(
        comodel_name='account.depara.plano',
        string='Referência Plano de Contas',
        help='Essa conta pertence a qual Plano de Contas?\n '
             'Se for o plano oficial deixar em branco',
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

    def identif_natureza_saldo(self, balance, natureza):
        """
        Identifica a natureza do saldo de acordo com o valor do balance e a
        natureza da conta.

        :param balance:
        :param natureza: 'C' or 'D'
        :return:
        """
        if balance == 0:
            return ''
        elif natureza == 'C':
            return 'credito' if balance > 0 else 'debito'
        elif natureza == 'D':
            return 'debito' if balance > 0 else 'credito'

        return ''

    @api.depends('balance')
    def _compute_saldo_conta(self):
        """
        Utilizar a natureza da conta para manipular o valor de saldo
        calculado automáticamente pela funcionalidade do core.

        obs: Este campo está substituindo o cambo 'balance' do core na visão
        """
        for record in self:
            record.saldo = abs(record.balance)
            record.identificacao_saldo = self.identif_natureza_saldo(
                record.balance, record.natureza_conta_id.name[0]) \
                if record.natureza_conta_id else ''

    @api.v7
    def _check_allow_code_change(self, cr, uid, ids, context=None):
        """
        :return:
        """
        if not self.user_has_groups(cr, uid, 'base.group_no_one'):
            return super(AccountAccount, self)._check_allow_code_change(
                cr, uid, ids, context=context)

    @api.multi
    def name_get(self):
        """
        Adicionar o nome do plano externo à conta
        """
        result = []

        for record in self:
            name = "{} {}".format(record.code, record.name)
            if record.account_depara_plano_id:
                name += " ({})".format(record.account_depara_plano_id.name)
            result.append((record.id, name))

        return result

    @api.model
    def create(self, vals):
        """
        """
        res = super(AccountAccount, self).create(vals)

        # Chamar a criação do ir.model.data mesmo pela interface, pois a
        # importação do depara é baseada nessa cara
        ident = res.account_depara_plano_id.name.upper() \
            if res.account_depara_plano_id else 'id'
        code = res.code.replace('.','_')

        # Para conta raiz. utilizar o name na identificacao
        if code == '0':
            ident = res.name

        self.env['ir.model.data'].create({
            'module': 'account',
            'name': 'account_account_{}_{}'.format(ident, code),
            'model': 'account.account',
            'res_id': res.id,
        })

        return res

    @api.multi
    def unlink(self):
        for record in self:
            ir_model_data = record.env['ir.model.data'].search([
                ('model', '=', 'account.account'),
                ('res_id', '=', record.id)
            ])

            ir_model_data.unlink()

            de_para_id = self.env['account.depara'].search(
                    [('conta_referencia_id', '=', record.id)])

            if de_para_id:
                raise Warning(
                    'Esta conta está relacionada em um De-Para, '
                    'por isso não pode ser Excluída!'
                )

            return super(AccountAccount, record).unlink()
