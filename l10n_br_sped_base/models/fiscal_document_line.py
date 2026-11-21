# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

from odoo import models


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    def _sped_tax_without_credit(self, tax_domain, cst):
        """An entry without credit right for ``tax_domain``: the CST the books
        carry grants the credit by its nature, but the company may not take it
        (regime, destination by the CFOP, Simples supplier). A CST that already
        says there is no credit (ICMS 40, IPI 02) is kept as it is.

        Only for a company whose ledger books the entry the same way
        (``res.company._books_entry_by_creditability``): any other credits the
        tax in the ledger, so the books carry the tax of the line."""
        self.ensure_one()
        return (
            bool(cst.default_creditable_tax)
            and self.company_id._books_entry_by_creditability()
            and self._get_tax_creditability_map()[tax_domain] == "cost"
        )

    def _get_sped_ipi_cst(self):
        """The IPI CST the books carry: the one of the entry when there is one,
        else the one of the line."""
        self.ensure_one()
        return self.entry_ipi_cst_id or self.ipi_cst_id

    def _sped_icms_without_credit(self):
        self.ensure_one()
        return self._sped_tax_without_credit("icms", self.icms_cst_id)

    def _sped_ipi_without_credit(self):
        self.ensure_one()
        return self._sped_tax_without_credit("ipi", self._get_sped_ipi_cst())

    def _get_sped_icms_values(self):
        """The ICMS of the line as the C170 carries it: the CST (origin plus the
        2 digits), the base, the rate and the value. An entry without credit
        right is CST of the origin plus 90 and no base, rate or value."""
        self.ensure_one()
        origin = self.icms_origin or "0"
        if self._sped_icms_without_credit():
            return {"cst": f"{origin}90", "base": 0.0, "percent": 0.0, "value": 0.0}
        return {
            "cst": f"{origin}{self.icms_cst_code or '00'}",
            "base": self.icms_base,
            "percent": self.icms_percent,
            "value": self.icms_value,
        }

    def _get_sped_ipi_values(self):
        """The IPI of the line as the C170 carries it: the CST, the base, the
        rate and the value. An entry without credit right is CST 49 (other
        entries) and no base, rate or value."""
        self.ensure_one()
        if self._sped_ipi_without_credit():
            return {"cst": "49", "base": 0.0, "percent": 0.0, "value": 0.0}
        return {
            "cst": self._get_sped_ipi_cst().code,
            "base": self.ipi_base,
            "percent": self.ipi_percent,
            "value": self.ipi_value,
        }
