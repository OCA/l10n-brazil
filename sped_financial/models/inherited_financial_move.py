# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class FinancialMove(models.Model):

    _inherit = 'financial.move'

    doc_source_id = fields.Reference(
        selection_add=[('sped.documento', 'Documento Fiscal')],
    )
