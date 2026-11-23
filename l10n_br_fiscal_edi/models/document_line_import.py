# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.l10n_br_fiscal.constants.fiscal import FISCAL_OUT


class DocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    def _find_or_create_supplierinfo(self):
        """The partner of a document the company issued is a customer: what the
        review of its lines teaches is not a mapping of a supplier."""
        received = self.filtered(
            lambda line: line.document_id.fiscal_operation_type != FISCAL_OUT
        )
        return super(DocumentLine, received)._find_or_create_supplierinfo()

    def _edi_import_product_vals(self):
        """Values of the product to create from the line of a document the company
        issued. The base takes what the line declares with certainty: the code, the
        description, the unit, the NCM, the CEST and the origin; a reader adds what
        its file declares (barcode, for instance). No category, no account."""
        self.ensure_one()
        vals = {
            "name": self.name,
            "default_code": self._get_partner_product_code(),
        }
        if self.uom_id:
            vals.update(uom_id=self.uom_id.id, uom_po_id=self.uom_id.id)
        if self.ncm_id:
            vals["ncm_id"] = self.ncm_id.id
        if self.cest_id:
            vals["cest_id"] = self.cest_id.id
        if self.icms_origin:
            vals["icms_origin"] = self.icms_origin
        return vals
