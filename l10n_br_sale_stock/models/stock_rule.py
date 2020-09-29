# Copyright (C) 2020 - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class StockRule(models.Model):
    """ A rule describe what a procurement should do; produce, buy, move,
    ... """
    _inherit = 'stock.rule'

    def _get_custom_move_fields(self):
        res = super(StockRule, self)._get_custom_move_fields()
        fiscal_fields = [key for key in self.env[
            'l10n_br_fiscal.document.line.mixin']._fields.keys()]
        res += fiscal_fields
        return res
