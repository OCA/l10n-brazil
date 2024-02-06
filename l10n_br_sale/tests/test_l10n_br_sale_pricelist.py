from odoo.tests import tagged
from odoo.tests.common import Form

from odoo.addons.sale.tests.common import TestSaleCommon


@tagged("post_install", "-at_install")
class TestSaleOrderPriceList(TestSaleCommon):
    @classmethod
    def setUpClass(
        cls, chart_template_ref="l10n_br_coa_generic.l10n_br_coa_generic_template"
    ):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.env.user.groups_id |= cls.env.ref("l10n_br_fiscal.group_manager")

        Pricelist = cls.env["product.pricelist"]
        PricelistItem = cls.env["product.pricelist.item"]
        SaleOrder = cls.env["sale.order"].with_context(tracking_disable=True)

        # Create a pricelist with especial price for partner_a
        cls.pricelist_partner_a = Pricelist.create(
            {
                "name": "Pricelist Partner A",
                "company_id": cls.company_data["company"].id,
            }
        )
        PricelistItem.create(
            {
                "pricelist_id": cls.pricelist_partner_a.id,
                "applied_on": "1_product",
                "product_tmpl_id": cls.company_data[
                    "product_order_no"
                ].product_tmpl_id.id,
                "compute_price": "fixed",
                "fixed_price": 10,
            }
        )

        cls.partner_a.with_company(
            cls.company_data["company"]
        ).property_product_pricelist = cls.pricelist_partner_a

        sale_form = Form(SaleOrder)
        sale_form.partner_id = cls.partner_a
        sale_form.fiscal_operation_id = cls.env.ref("l10n_br_fiscal.fo_venda")

        with sale_form.order_line.new() as line_form:
            line_form.name = cls.company_data["product_order_no"].name
            line_form.product_id = cls.company_data["product_order_no"]
            line_form.fiscal_operation_line_id = cls.env.ref(
                "l10n_br_fiscal.fo_venda_revenda"
            )

        cls.sale_order = sale_form.save()

    def test_pricelist_onchange_product(self):
        """Test pricelist onchange product_id"""

        # prices before product change.
        price_before = self.sale_order.order_line[0].price_unit
        fiscal_price_before = self.sale_order.order_line[0].fiscal_price

        # change product name
        with Form(self.sale_order) as sale_form:
            with sale_form.order_line.edit(0) as line_form:
                line_form.product_id.name = "Test Product - New Name"
        self.sale_order = sale_form.save()

        # onchange must be called to follow the same behavior as the view.
        self.sale_order.order_line._onchange_product_id_fiscal()

        # prices after product change.
        price_after = self.sale_order.order_line[0].price_unit
        fiscal_price_after = self.sale_order.order_line[0].fiscal_price

        # check if prices are the same.
        self.assertEqual(price_before, price_after)
        self.assertEqual(fiscal_price_before, fiscal_price_after)
