# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import Warning

MODELS = [
    ('hr.salary.rule', 'Rúbricas Holerite'),
    ('account.tax', 'Impostos'),
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
