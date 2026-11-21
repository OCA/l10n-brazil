# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    def _nfse_foreign_currency_rate(self):
        """Use the rate of the invoice the NFS-e comes from.

        ``account.move.invoice_currency_rate`` is the rate from the company
        currency to the invoice currency (so, 1 BRL = 0.204 USD), and on Odoo
        18 it already holds the manual rate when account_manual_currency is
        used. The multiplier to reais is its inverse.
        """
        self.ensure_one()
        move = self.move_ids.filtered(
            lambda m: m.currency_id != m.company_currency_id and m.invoice_currency_rate
        )[:1]
        if not move:
            return super()._nfse_foreign_currency_rate()
        return move.currency_id, round(1.0 / move.invoice_currency_rate, 10)
