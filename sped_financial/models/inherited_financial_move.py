# -*- coding: utf-8 -*-
#
#  Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _


class FinancialMove(models.Model):
    _inherit = 'financial.move'

    doc_source_id = fields.Reference(
        selection_add=[('sped.documento', 'Documento Fiscal')],
    )
    documento_id = fields.Many2one(
        comodel_name='sped.documento',
        string='Documento Fiscal',
        ondelete='restrict',
    )
    documento_duplicata_id = fields.Many2one(
        comodel_name='sped.documento.duplicata',
        string='Duplicata do Documento Fiscal',
        ondelete='restrict',
    )

    @api.depends('date_maturity')
    def _compute_date_business_maturity(self):
        for move in self:
            if (not move.date_maturity) or \
                (not move.company_id.country_id) or \
                (move.company_id.country_id.id != self.env.ref('base.br').id):
                super(FinancialMove, move)._compute_date_business_maturity()
                continue

            date_maturity = fields.Date.from_string(move.date_maturity)
            date_business_maturity = \
                self.env['resource.calendar'].proximo_dia_util_bancario(
                    date_maturity
                )
            move.date_business_maturity = date_business_maturity
