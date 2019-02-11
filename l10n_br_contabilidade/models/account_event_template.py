# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountEventTemplate(models.Model):
    _name = 'account.event.template'

    name = fields.Char(
        string='Nome',
    )

    lote_lancamento_id = fields.Many2one(
        string=u'Lote de Lançamentos',
        comodel_name='account.journal',
    )

    account_formula = fields.Selection(
        string=u'Fórmula',
        selection=[
            (1, '1ª Fórumla'),
            (2, '2ª Fórumla'),
            (3, '3ª Fórumla'),
            (4, '4ª Fórumla'),
        ],
    )

    account_event_template_line_ids = fields.One2many(
        string='Partidas',
        comodel_name='account.event.template.line',
        inverse_name='account_event_template_id',
    )
