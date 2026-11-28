# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockInvoiceOnshipping(models.TransientModel):
    _inherit = "stock.invoice.onshipping"

    def _loyalty_fold_weights(self, targets, fname):
        """Distribute a free-shipping reward over the freight the invoice lines
        already carry, so it zeroes out exactly (l10n_br_delivery spreads the
        freight over the product lines, not over a delivery line).
        """
        if fname == "freight_value":
            return [abs(vals.get("freight_value") or 0.0) for vals in targets]
        return super()._loyalty_fold_weights(targets, fname)
