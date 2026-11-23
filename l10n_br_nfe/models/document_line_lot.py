# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.l10n_br_fiscal_edi.tools import EdiLot


class DocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    def _edi_get_lots(self):
        """The lots (``rastro``) the NF-e declares for the item: number,
        quantity in the unit of the item, manufacturing and expiry dates."""
        self.ensure_one()
        lots = [
            EdiLot(
                name=rastro.nfe40_nLote,
                quantity=rastro.nfe40_qLote,
                date_manufacture=rastro.nfe40_dFab or None,
                date_expiry=rastro.nfe40_dVal or None,
            )
            for rastro in self.nfe40_rastro
        ]
        return lots or super()._edi_get_lots()
