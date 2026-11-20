# Copyright (C) 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class FakeStockPriceLine(models.Model):
    """Smallest concrete line carrying the net acquisition cost mixin.

    The mixin has no consumer inside l10n_br_fiscal (stock.move and the
    purchase order line live in other modules), so this fake line is the
    fiscal line mixin plus the stock price mixin, and nothing else.
    """

    _name = "l10n_br_fiscal.test.cost.line"
    _description = "Fake Line for the Stock Price Mixin Tests"
    _inherit = [
        "l10n_br_fiscal.document.line.mixin",
        "l10n_br_fiscal.stock.price.mixin",
    ]

    def _get_document(self):
        self.ensure_one()
        return self.env["l10n_br_fiscal.document"]
