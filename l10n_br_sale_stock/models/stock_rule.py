# Copyright (C) 2020 - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class StockRule(models.Model):
    """ A rule describe what a procurement should do; produce, buy, move, ... """
    _inherit = 'stock.rule'

    def _get_custom_move_fields(self):
        res = super(StockRule, self)._get_custom_move_fields()
        return res + ['freight_value']
