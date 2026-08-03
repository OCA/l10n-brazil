# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.stock_picking_invoicing.tests.common import TestPickingInvoicingCommon


class TestBrPickingInvoicingCommon(TestPickingInvoicingCommon):
    def _change_user_company(self, company):
        self.env.user.company_ids += company
        self.env.user.company_id = company

    def _run_line_onchanges(self, record):
        result = super()._run_line_onchanges(record)
        record._onchange_product_quantity()
        return result

    def _assert_tax_fields_match_recompute(self, invoice_lines):
        """Assert the stored tax fields match a fresh recompute.

        They are stored compute fields with readonly=False, so an explicit
        value given at create() is kept as is and the compute is skipped.
        When such a value was calculated on another quantity, the fiscal
        amounts and the journal entry tax lines stop matching each other.
        """
        tax_fields = (
            "icms_base",
            "icms_value",
            "icmssn_base",
            "icmssn_credit_value",
            "ipi_base",
            "ipi_value",
            "pis_base",
            "pis_value",
            "cofins_base",
            "cofins_value",
            "amount_tax_included",
            "amount_tax_not_included",
            "amount_tax_withholding",
        )
        for invoice_line in invoice_lines:
            fiscal_line = invoice_line.fiscal_document_line_id
            stored = {name: fiscal_line[name] for name in tax_fields}
            fiscal_line._compute_tax_fields()
            for name, value in stored.items():
                self.assertAlmostEqual(
                    fiscal_line[name],
                    value,
                    2,
                    f"{name} differs after recompute: stored={value}, "
                    f"recomputed={fiscal_line[name]}",
                )
