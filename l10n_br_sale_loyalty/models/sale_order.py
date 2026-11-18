# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_invoiceable_lines(self, final=False):
        """Never invoice a folded discount reward line on its own: its value is
        carried by the fiscal discount of the lines it discounts, applied when
        the invoice is generated from the delivery.
        """
        lines = super()._get_invoiceable_lines(final=final)
        return lines.filtered(lambda ln: not ln._loyalty_folds_into_invoice())
