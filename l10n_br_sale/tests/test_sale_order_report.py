# Copyright (C) 2025-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests import Form, TransactionCase, tagged

from odoo.addons.sale.tests.common import TestSaleCommon

from .tools import load_sale_fixture_files


@tagged("post_install", "-at_install")
class TestSaleReport(TestSaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # TestSaleCommon enables the pricelists group on the user, but the
        # group membership cache (res.users has_group / _get_group_ids) is a
        # registry level cache: without clearing it the Form still considers
        # pricelist_id as invisible (groups="product.group_product_pricelist")
        # and refuses to write it.
        cls.env.registry.clear_all_caches()

        # The Brazilian fiscal fields of the sale order form are injected and
        # displayed only for a Brazilian company: Odoo 19 stores the company
        # country on the company partner, so set the Brazilian address there.
        company = cls.company_data["company"]
        company.partner_id.write(
            {
                "country_id": cls.env.ref("base.br").id,
                "state_id": cls.env.ref("base.state_br_sp").id,
            }
        )

        # The Brazilian fiscal fields of the sale order form are only visible
        # when the form company is a Brazilian company, and the sale order has
        # to be created in the Brazilian test company (env.company is the main
        # company of the test user).
        sale_form = Form(
            cls.env["sale.order"].with_context(
                allowed_company_ids=cls.company_data["company"].ids
            )
        )
        sale_form.partner_id = cls.partner_a
        sale_form.fiscal_operation_id = cls.env.ref("l10n_br_fiscal.fo_venda")
        with sale_form.order_line.new() as line:
            line.name = cls.company_data["product_order_no"].name
            line.product_id = cls.company_data["product_order_no"]
            line.fiscal_operation_id = cls.env.ref("l10n_br_fiscal.fo_venda")
            line.fiscal_operation_line_id = cls.env.ref("l10n_br_fiscal.fo_venda_venda")
            line.price_unit = cls.company_data["product_order_no"].list_price
            line.product_uom_qty = 3
        sale_form.save()

    def test_sale_br_report_sale_order(self):
        """Test Sale Report for Brazil Case"""
        self.env["sale.report"]._read_group(
            [("product_id", "!=", False)],
            ["fiscal_operation_id"],
            ["product_uom_qty:sum", "price_total:sum"],
        )


class TestSaleReportFiscal(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_sale_fixture_files(cls.env)
        cls.order = cls.env.ref("l10n_br_sale.lc_so_only_products")
        cls.lines = cls.order.order_line.filtered(lambda line: not line.display_type)
        cls.lines[0].freight_value = 10.0
        cls.report = cls.env["sale.report"].with_company(cls.order.company_id)

    def test_fiscal_values(self):
        self.env.flush_all()
        rows = self.report.search(
            [("order_reference", "=", f"sale.order,{self.order.id}")]
        )
        for fname in ("icms_value", "ipi_value", "freight_value"):
            self.assertAlmostEqual(
                sum(rows.mapped(fname)), sum(self.lines.mapped(fname)), places=2
            )
        # price_total already has IPI, ST, freight, insurance and other costs
        self.assertAlmostEqual(
            sum(rows.mapped("total_with_taxes")),
            sum(self.lines.mapped("price_total"))
            + sum(self.lines.mapped("amount_tax_withholding")),
            places=2,
        )

    def test_search_view_filters(self):
        arch = self.report.get_views([(False, "search")])["views"]["search"]["arch"]
        names = set(etree.fromstring(arch).xpath("//filter/@name"))
        self.assertIn("fiscal_out", names)
        # sale orders have no electronic document situation
        self.assertNotIn("fiscal_edoc_not_void", names)
