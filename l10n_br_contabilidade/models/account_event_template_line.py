# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
from openerp.exceptions import Warning

MODELS = [
    ('hr.salary.rule', 'Rúbricas Holerite'),
    ('account.invoice', 'Nota Fiscal'),
]


class AccountEventTemplateLine(models.Model):
    _name = 'account.event.template.line'

    account_event_template_id = fields.Many2one(
        string='Partidas',
        comodel_name='account.event.template',
    )

    res_id = fields.Reference(
        selection=MODELS,
        string=u'Rúbrica da partida',
    )

    codigo = fields.Char(
        string=u'Código',
    )

    account_debito_id = fields.Many2one(
        string=u'Conta Débito',
        comodel_name='account.account',
        domain=[('type', '=', 'other')],
    )

    account_credito_id = fields.Many2one(
        string=u'Conta Crédito',
        comodel_name='account.account',
        domain=[('type', '=', 'other')],
    )

    account_historico_padrao_id = fields.Many2one(
        comodel_name='account.historico.padrao',
        string='Histórico Padrão'
    )

    account_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string=u'Lote de Lançamentos',
    )

    def validar_identificacao_partida(self):
        if self.res_id and self.codigo:
            raise Warning(
                'Uma partida não pode possuir uma '
                'rúbrica e um código ao mesmo tempo!'
            )

    def validar_contas_partida(self):
        if self.account_debito_id == self.account_credito_id:
            raise Warning(
                'Uma partida não pode possuir uma conta de débito '
                'igual a uma conta de crédito!'
            )

    def validar_partida(self):
        self.validar_identificacao_partida()
        self.validar_contas_partida()

    # @api.model
    # def create(self, vals):
    #     res = super(AccountEventTemplateLine, self).create(vals)
    #     res.validar_partida()
    #     return res
    #
    # @api.multi
    # def write(self, vals):
    #     res = super(AccountEventTemplateLine, self).write(vals)
    #     self.validar_partida()
    #     return res

    @api.onchange('account_journal_id')
    def set_journal_defaults(self):
        self.account_debito_id = \
            self.account_journal_id.default_debit_account_id.id if \
            self.account_journal_id.default_debit_account_id else False
        self.account_credito_id = \
            self.account_journal_id.default_credit_account_id.id if \
            self.account_journal_id.default_credit_account_id else False
        self.account_historico_padrao_id = \
            self.account_journal_id.template_historico_padrao_id.id if \
            self.account_journal_id.template_historico_padrao_id else False

    @api.constrains('codigo')
    def _codigo_unique(self):
        if len(self.search([('codigo', '=', self.codigo)])) > 1:
            raise Warning(_('Codigo precisa ser único!'))
