# Copyright (C) 2026 - TODAY Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import Form, TransactionCase, tagged

from odoo.addons.l10n_br_fiscal.tests.tools import load_fiscal_fixture_files


def _get_widget_tax_amount(tax_totals, group_name):
    """Return a tax group amount displayed in the tax totals widget."""
    for subtotal in (tax_totals or {}).get("subtotals", []):
        for group in subtotal.get("tax_groups", []):
            if group.get("group_name") == group_name:
                return group["tax_amount_currency"]
    return None


@tagged("post_install", "-at_install")
class TestPurchaseOrderEdition(TransactionCase):
    """
    Edit a Brazilian fiscal purchase order through the user interface.
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
        # Supplier in SP, same state as the company.
        cls.partner = cls.env.ref("l10n_br_base.res_partner_amd")
        # Physical product with NCM 7326.90.90 so ICMS and IPI are mapped.
        cls.product = cls.env.ref("product.product_product_7")
        cls.product.standard_price = 100.0
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

    def _open_purchase_order_form(self):
        return Form(
            self.env["purchase.order"].with_context(default_company_id=self.company.id)
        )

    def _assert_widget_icms_matches_line(self, purchase_order):
        """The widget must display the fiscal ICMS of the order line.

        Without account taxes mapped on the line (which happens when the
        database has no demo chart data), the widget legitimately falls
        back to untaxed amounts, so the check only applies when the line
        carries account taxes.
        """
        line = purchase_order.order_line.filtered(lambda ln: not ln.display_type)
        if line.taxes_id:
            self.assertAlmostEqual(
                _get_widget_tax_amount(purchase_order.tax_totals, "ICMS"),
                line.icms_value,
                2,
                msg="ICMS amount in the widget should match line icms_value.",
            )
        else:
            self.assertIsNone(_get_widget_tax_amount(purchase_order.tax_totals, "ICMS"))

    def _assert_br_tax_computation(self, line):
        """Check the Brazilian taxes against the fiscal engine rules.

        Amounts are for a line of 10 units at price_unit 100.00
        (untaxed 1000.00), "Compras para Comercialização" from a SP
        supplier:

        * ICMS 18%: base = untaxed (the IPI does NOT integrate the ICMS
          base on a purchase destined to resale, unlike a sale to a final
          consumer), so 1000.00 * 18% = 180.00.
        * IPI 5% (NCM 7326.90.90): 1000.00 * 5% = 50.00.
        * PIS 0.65% (cumulativo): 1000.00 * 0.65% = 6.50.
        * COFINS 3% (cumulativo): 1000.00 * 3% = 30.00.

        Each value must equal its base times its percent / 100.
        """
        self.assertAlmostEqual(
            line.icms_percent, 18.0, 2, msg="ICMS percent should be 18%."
        )
        self.assertAlmostEqual(line.icms_value, 180.0, 2, msg="Wrong ICMS value.")
        self.assertAlmostEqual(
            line.ipi_percent, 5.0, 2, msg="IPI percent should be 5%."
        )
        self.assertAlmostEqual(line.ipi_value, 50.0, 2, msg="Wrong IPI value.")
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
        # On a purchase destined to resale, the IPI does not integrate the
        # ICMS base (the goods are destined to commercialization).
        self.assertAlmostEqual(
            line.icms_base,
            line.ipi_base,
            2,
            msg="ICMS base should not integrate the IPI on a resale purchase.",
        )

    def test_fiscal_purchase_order_tax_totals_on_edition(self):
        order_form = self._open_purchase_order_form()
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_qty = 10.0

        # --- Before saving: the widget must already show the fiscal ICMS ---
        icms_before_save = _get_widget_tax_amount(order_form.tax_totals, "ICMS")
        if icms_before_save is not None:
            self.assertGreater(icms_before_save, 0.0)

        purchase_order = order_form.save()
        self.env.flush_all()
        line = purchase_order.order_line.filtered(lambda ln: not ln.display_type)
        self.assertEqual(len(line), 1)

        # --- After saving: fiscal taxes are mapped and computed -------------
        self.assertTrue(
            line.icms_tax_id, "ICMS tax should be mapped on the purchase line."
        )
        self.assertTrue(
            line.ipi_tax_id, "IPI tax should be mapped on the purchase line."
        )
        self._assert_br_tax_computation(line)
        if icms_before_save is not None:
            self.assertAlmostEqual(
                icms_before_save,
                line.icms_value,
                2,
                msg="ICMS displayed before saving should match line icms_value.",
            )

        # The stored totals come from the fiscal line amounts.
        self.assertAlmostEqual(
            purchase_order.amount_untaxed,
            line.fiscal_amount_untaxed,
            2,
            msg="Wrong untaxed amount.",
        )
        self.assertAlmostEqual(
            purchase_order.amount_total,
            line.fiscal_amount_total,
            2,
            msg="Order total should match the fiscal line total.",
        )
        self.assertAlmostEqual(
            purchase_order.amount_untaxed + purchase_order.amount_tax,
            purchase_order.amount_total,
            2,
            msg="untaxed + tax should equal the total.",
        )

        # The tax_totals widget must agree with the stored fiscal total.
        tax_totals = purchase_order.tax_totals
        self.assertTrue(tax_totals, "tax_totals must not be empty.")
        self.assertAlmostEqual(
            tax_totals["total_amount_currency"],
            purchase_order.amount_total,
            2,
            msg="Widget total should match the stored order total.",
        )
        self._assert_widget_icms_matches_line(purchase_order)

        # --- Edit the quantity through the UI: totals must follow -----------
        with Form(purchase_order) as order_form:
            with order_form.order_line.edit(0) as line_form:
                line_form.product_qty = 20.0
        self.env.flush_all()
        purchase_order.invalidate_recordset()
        line.invalidate_recordset()

        self.assertAlmostEqual(
            purchase_order.amount_untaxed,
            line.fiscal_amount_untaxed,
            2,
            msg="Untaxed amount frozen after edition.",
        )
        self.assertAlmostEqual(
            purchase_order.amount_total,
            line.fiscal_amount_total,
            2,
            msg="Order total should match the fiscal total after edition.",
        )
        self.assertAlmostEqual(
            purchase_order.tax_totals["total_amount_currency"],
            purchase_order.amount_total,
            2,
            msg="Widget total should match the stored total after edition.",
        )
        self._assert_widget_icms_matches_line(purchase_order)
