# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountEventTemplate(models.Model):
    _name = 'account.event.template.line'

    name = fields.Char(
        string='Nome',
    )

    account_event_template_id = fields.Many2one(
        string='Partidas',
        comodel_name='account.event.template',
    )

    model_id = fields.Many2one(
        comodel_name='ir.model',
        string='Model',
    )

    res_id = fields.Reference(
        selection=lambda self: [
            (m.model, m.name) for m in self.env['ir.model'].search([])
        ],
        string='Resource',
    )

    codigo = fields.Char(
        string=u'Código',
    )

    account_debito_id = fields.Many2one(
        string=u'Conta Débito',
        comodel_name='account.account',
    )

    account_credito_id = fields.Many2one(
        string=u'Conta Crédito',
        comodel_name='account.account',
    )

    valor = fields.Float(
        string='Valor',
    )
