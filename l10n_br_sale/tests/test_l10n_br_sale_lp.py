from odoo.tests import TransactionCase

from .test_l10n_br_sale import L10nBrSaleBaseTest


class TestL10nBrSale(L10nBrSaleBaseTest, TransactionCase):
    __test__ = True

    company_ref = "l10n_br_base.empresa_lucro_presumido"
    so_products_ref = "l10n_br_sale.lc_so_only_products"
    so_services_ref = "l10n_br_sale.lc_so_only_services"
    so_product_service_ref = "l10n_br_sale.lc_so_product_service"

    def test_partial_invoice_fiscal_quantity(self):
        """Test fiscal_quantity on partial invoices with delivery policy."""
        self._change_user_company(self.company)
        self._run_sale_order_onchanges(self.so_products)
        so_lines = self.so_products.order_line.filtered(
            lambda line: not line.display_type
        )
        self.assertTrue(so_lines, "SO must have product lines")
        for line in so_lines:
            self._run_sale_line_onchanges(line)
            line.product_id.invoice_policy = "delivery"

        self.so_products.action_confirm()

        # First delivery: half
        for line in so_lines:
            line.qty_delivered = line.product_uom_qty / 2.0

        # First invoice
        self.so_products._create_invoices()
        first_invoice = self.so_products.invoice_ids[0]
        inv_lines = first_invoice.invoice_line_ids.filtered(
            lambda line: line.display_type == "product"
        )
        self.assertTrue(inv_lines, "Invoice must have product lines")
        for inv_line in inv_lines:
            so_line = inv_line.sale_line_ids[0]
            uot_factor = so_line.product_id.uot_factor or 1.0
            expected_qty = so_line.product_uom_qty / 2.0
            expected_fiscal_qty = expected_qty * uot_factor
            self.assertAlmostEqual(inv_line.quantity, expected_qty, 2)
            self.assertAlmostEqual(inv_line.fiscal_quantity, expected_fiscal_qty, 2)

        # Stored compute fields populated by _compute_tax_fields must match a
        # fresh recompute. If they differ, _prepare_invoice_line is copying
        # frozen values from the SO line (computed for the full ordered qty)
        # and the ORM is skipping the compute because the values were passed
        # explicitly at create().
        self._assert_tax_fields_match_recompute(inv_lines)

        first_invoice.action_post()

        # Second delivery: remaining half
        for line in so_lines:
            line.qty_delivered = line.product_uom_qty

        # Second invoice
        self.so_products._create_invoices()
        second_invoice = self.so_products.invoice_ids.filtered(
            lambda inv: inv.id != first_invoice.id
        )[0]
        inv_lines = second_invoice.invoice_line_ids.filtered(
            lambda line: line.display_type == "product"
        )
        self.assertTrue(inv_lines, "Second invoice must have product lines")
        for inv_line in inv_lines:
            so_line = inv_line.sale_line_ids[0]
            uot_factor = so_line.product_id.uot_factor or 1.0
            expected_qty = so_line.product_uom_qty / 2.0
            expected_fiscal_qty = expected_qty * uot_factor
            self.assertAlmostEqual(inv_line.quantity, expected_qty, 2)
            self.assertAlmostEqual(inv_line.fiscal_quantity, expected_fiscal_qty, 2)

        self._assert_tax_fields_match_recompute(inv_lines)

    def _assert_tax_fields_match_recompute(self, inv_lines):
        """Assert each fiscal.document.line stored value populated by
        _compute_tax_fields matches what a fresh recompute produces.

        Mismatch indicates the value was copied frozen from the SO line at
        invoice creation rather than computed for the actually-invoiced
        quantity.
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
        )
        for inv_line in inv_lines:
            fdl = inv_line.fiscal_document_line_id
            before = {f: fdl[f] for f in tax_fields}
            fdl._compute_tax_fields()
            for f, stored in before.items():
                self.assertAlmostEqual(
                    fdl[f],
                    stored,
                    2,
                    f"{f} on invoice line for {inv_line.product_id.display_name}: "
                    f"stored={stored}, recomputed={fdl[f]} — compute field was "
                    f"copied frozen from SO line instead of computed for the "
                    f"invoiced quantity",
                )
