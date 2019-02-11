# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models

MODELS = [
    ('hr.salary.rule', 'Rúbricas Holerite'),
    ('account.tax', 'Impostos'),
]


class AccountEventTemplate(models.Model):
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

    partida_especifica = fields.Boolean(
        string=u'Específica',
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

    valor = fields.Float(
        string='Valor',
    )
