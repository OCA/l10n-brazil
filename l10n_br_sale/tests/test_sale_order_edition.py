# Copyright (C) 2026 - TODAY Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import Form, TransactionCase, new_test_user, tagged, users


@tagged("post_install", "-at_install")
class TestSaleOrderEdition(TransactionCase):
    """
    Edit a Brazilian fiscal sale order through the user interface.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        new_test_user(
            cls.env,
            login="l10n_br_sale_salesman",
            groups="sales_team.group_sale_salesman",
            company_id=cls.company.id,
        )
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
        for tax in ("icms", "ipi", "pis", "cofins"):
            self.assertAlmostEqual(
                line[f"{tax}_value"],
                line[f"{tax}_base"] * line[f"{tax}_percent"] / 100.0,
                2,
                msg=f"{tax.upper()} value must equal base * percent / 100.",
            )
        # ICMS base integrates the IPI (non-contribuinte final consumer).
        self.assertAlmostEqual(
            line.icms_base,
            line.ipi_base + line.ipi_value,
            2,
            msg="ICMS base should integrate the IPI value.",
        )

    def test_fiscal_sale_order_amounts_on_edition(self):
        order_form = self._open_sale_order_form()
        order_form.partner_id = self.partner
        order_form.fiscal_operation_id = self.fiscal_operation
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 2.0
            line_form.price_unit = 500.0
            line_form.fiscal_operation_line_id = self.fiscal_operation_line
        sale_order = order_form.save()
        self.env.flush_all()
        line = sale_order.order_line.filtered(lambda ln: not ln.display_type)
        self.assertEqual(len(line), 1)

        self.assertTrue(line.icms_tax_id, "ICMS tax should be mapped on the sale line.")
        self.assertTrue(line.ipi_tax_id, "IPI tax should be mapped on the sale line.")
        self._assert_br_tax_computation(line)
        self.assertAlmostEqual(
            sale_order.amount_untaxed, 1000.0, 2, msg="Wrong untaxed amount."
        )
        self.assertAlmostEqual(
            sale_order.amount_total,
            sale_order.amount_untaxed + sale_order.amount_tax,
            2,
            msg="untaxed + tax should equal the total.",
        )

        # Edit the price through the UI: totals must follow (not frozen).
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

    @users("l10n_br_sale_salesman")
    def test_fiscal_sale_order_amounts_on_edition_salesman(self):
        self.test_fiscal_sale_order_amounts_on_edition()
