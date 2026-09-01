# Copyright (C) 2026 - TODAY Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import Form, TransactionCase, tagged

from odoo.addons.l10n_br_fiscal.tests.tools import load_fiscal_fixture_files


def _get_widget_icms(tax_totals):
    """Return the ICMS tax amount displayed in the tax totals widget."""
    for subtotal in (tax_totals or {}).get("subtotals", []):
        for group in subtotal.get("tax_groups", []):
            if group.get("group_name") == "ICMS":
                return group["tax_amount_currency"]
    return None


@tagged("post_install", "-at_install")
class TestSaleOrderEdition(TransactionCase):
    """Edit a Brazilian fiscal sale order through the user interface.

    In Odoo 18, sale.order.amount_untaxed/amount_total are computed by the
    native tax engine: sale._compute_amounts() reads the values back from
    AccountTax._get_tax_totals_summary(). This test edits a fiscal sale
    order through the Form (UI flow) and checks the tax totals widget
    (ICMS included) and the stored totals, both before and after saving,
    so a broken feedback loop between _get_tax_totals_summary() and the
    stored order amounts cannot go unnoticed.

    The line-level Brazilian taxes are checked against the fiscal engine:
    a physical product (NCM 9403.30.00) sold to a non-contribuinte final
    consumer (ind_ie_dest = 9) from the empresa_lucro_presumido company
    (tax framework "normal", cumulativo), through fo_venda/fo_venda_venda.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Load the demo companies/partners/products/taxes as fixtures so the
        # test does not depend on the database being installed with demo data.
        load_fiscal_fixture_files(cls.env)
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids)
        )
        cls.env.user.company_ids += cls.company
        cls.env.user.company_id = cls.company
        cls.partner = cls.env.ref("l10n_br_base.res_partner_akretion")
        # Physical product with NCM 9403.30.00 so ICMS and IPI are mapped.
        cls.product = cls.env.ref("product.product_product_27")
        cls.fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.fiscal_operation_line = cls.env.ref("l10n_br_fiscal.fo_venda_venda")
        # Ensure the company has a warehouse when stock is installed.
        if "stock.warehouse" in cls.env:
            if not cls.env["stock.warehouse"].search(
                [("company_id", "=", cls.company.id)], limit=1
            ):
                cls.env["stock.warehouse"].create(
                    {
                        "name": cls.company.name,
                        "code": cls.company.name[:5],
                        "company_id": cls.company.id,
                    }
                )

    def _open_sale_order_form(self):
        return Form(
            self.env["sale.order"].with_context(default_company_id=self.company.id)
        )

    def _assert_widget_icms_matches_line(self, sale_order):
        """The widget must display the fiscal ICMS of the order line.

        Without account taxes mapped on the line (which happens when the
        database has no demo chart data), the widget legitimately falls
        back to untaxed amounts, so the check only applies when the line
        carries account taxes.
        """
        line = sale_order.order_line.filtered(lambda ln: not ln.display_type)
        if line.tax_id:
            self.assertAlmostEqual(
                _get_widget_icms(sale_order.tax_totals),
                line.icms_value,
                2,
                msg="ICMS amount in the widget should match line icms_value.",
            )
        else:
            self.assertIsNone(_get_widget_icms(sale_order.tax_totals))

    def _assert_br_tax_computation(self, line):
        """Check the Brazilian taxes against the fiscal engine rules.

        Amounts are for a line of 2 units at price_unit 500.00
        (untaxed 1000.00):

        * ICMS 12%: base = untaxed + IPI (IPI integrates the ICMS base
          when selling to a non-contribuinte final consumer), so
          1032.50 * 12% = 123.90.
        * IPI 3.25% (NCM 9403.30.00): 1000.00 * 3.25% = 32.50.
        * PIS 0.65% (cumulativo): 1000.00 * 0.65% = 6.50.
        * COFINS 3% (cumulativo): 1000.00 * 3% = 30.00.

        Each value must equal its base times its percent / 100.
        """
        self.assertAlmostEqual(
            line.icms_percent, 12.0, 2, msg="ICMS percent should be 12%."
        )
        self.assertAlmostEqual(line.icms_value, 123.9, 2, msg="Wrong ICMS value.")
        self.assertAlmostEqual(
            line.ipi_percent, 3.25, 2, msg="IPI percent should be 3.25%."
        )
        self.assertAlmostEqual(line.ipi_value, 32.5, 2, msg="Wrong IPI value.")
        self.assertGreater(line.pis_value, 0.0, "PIS value should be positive.")
        self.assertGreater(line.cofins_value, 0.0, "COFINS value should be positive.")
        # Cross-check the fiscal rule value = base * percent / 100.
        self.assertAlmostEqual(
            line.icms_value,
            line.icms_base * line.icms_percent / 100.0,
            2,
            msg="ICMS value must equal base * percent / 100.",
        )
        self.assertAlmostEqual(
            line.ipi_value,
            line.ipi_base * line.ipi_percent / 100.0,
            2,
            msg="IPI value must equal base * percent / 100.",
        )
        self.assertAlmostEqual(
            line.pis_value,
            line.pis_base * line.pis_percent / 100.0,
            2,
            msg="PIS value must equal base * percent / 100.",
        )
        self.assertAlmostEqual(
            line.cofins_value,
            line.cofins_base * line.cofins_percent / 100.0,
            2,
            msg="COFINS value must equal base * percent / 100.",
        )
        # ICMS base integrates the IPI (non-contribuinte final consumer).
        self.assertAlmostEqual(
            line.icms_base,
            line.ipi_base + line.ipi_value,
            2,
            msg="ICMS base should integrate the IPI value.",
        )

    def test_fiscal_sale_order_tax_totals_on_edition(self):
        order_form = self._open_sale_order_form()
        order_form.partner_id = self.partner
        order_form.fiscal_operation_id = self.fiscal_operation
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 2.0
            line_form.price_unit = 500.0
            line_form.fiscal_operation_line_id = self.fiscal_operation_line

        # --- Before saving: the widget must already show the fiscal taxes ---
        icms_before_save = _get_widget_icms(order_form.tax_totals)
        if icms_before_save is not None:
            self.assertGreater(icms_before_save, 0.0)

        sale_order = order_form.save()
        self.env.flush_all()
        line = sale_order.order_line.filtered(lambda ln: not ln.display_type)
        self.assertEqual(len(line), 1)

        # --- After saving: fiscal taxes are mapped and computed -------------
        self.assertTrue(line.icms_tax_id, "ICMS tax should be mapped on the sale line.")
        self.assertTrue(line.ipi_tax_id, "IPI tax should be mapped on the sale line.")
        self._assert_br_tax_computation(line)
        if icms_before_save is not None:
            self.assertAlmostEqual(
                icms_before_save,
                line.icms_value,
                2,
                msg="ICMS displayed before saving should match line" " icms_value.",
            )
        self.assertAlmostEqual(
            sale_order.amount_untaxed, 1000.0, 2, msg="Wrong untaxed amount."
        )
        self.assertAlmostEqual(
            sale_order.amount_total,
            sale_order.amount_untaxed + sale_order.amount_tax,
            2,
            msg="untaxed + tax should equal the total.",
        )

        # The tax_totals widget should agree with the stored total.
        tax_totals = sale_order.tax_totals
        self.assertTrue(tax_totals, "tax_totals must not be empty.")
        self.assertAlmostEqual(
            tax_totals["total_amount_currency"],
            sale_order.amount_total,
            2,
            msg="Widget total should match the stored order total.",
        )
        self._assert_widget_icms_matches_line(sale_order)

        # --- Edit the price through the UI: totals must follow (not frozen) --
        with Form(sale_order) as order_form:
            with order_form.order_line.edit(0) as line_form:
                line_form.price_unit = 700.0
        self.env.flush_all()
        sale_order.invalidate_recordset()
        line.invalidate_recordset()

        self.assertAlmostEqual(
            sale_order.amount_untaxed, 1400.0, 2, msg="Untaxed amount frozen."
        )
        self.assertAlmostEqual(
            sale_order.amount_total,
            sale_order.amount_untaxed + sale_order.amount_tax,
            2,
            msg="untaxed + tax should equal the total after edition.",
        )
        self.assertAlmostEqual(
            sale_order.tax_totals["total_amount_currency"],
            sale_order.amount_total,
            2,
            msg="Widget total should match the stored total after edition.",
        )
        self._assert_widget_icms_matches_line(sale_order)
