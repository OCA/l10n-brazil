# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _


class FinancialMove(models.Model):

    _inherit = b'financial.move'

    tipo_documento = fields.Many2one(
        string='Tipo do documento',
        comodel_name=b'financeiro.tipo_documento',
    )
