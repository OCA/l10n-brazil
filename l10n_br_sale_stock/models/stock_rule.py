# Copyright (C) 2020 - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class StockRule(models.Model):
    """ A rule describe what a procurement should do; produce, buy, move,
    ... """
    _inherit = 'stock.rule'

    def _get_custom_move_fields(self):
        res = super(StockRule, self)._get_custom_move_fields()
        res += [
            'freight_value',
            'insurance_value',
            'other_costs_value',
            'cofins_tax_id',
            'cofins_cst_id',
            'pis_tax_id',
            'pis_cst_id',
            'ipi_tax_id',
            'ipi_cst_id',
            'icmssn_tax_id',
            'icms_tax_id',
            'icms_cst_id',
            ]
        return res
