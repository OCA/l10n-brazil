from odoo.tests import Form, tagged

from odoo.addons.sale.tests.common import TestSaleCommon


@tagged("post_install", "-at_install")
class TestSaleOrderPriceList(TestSaleCommon):
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
        cls.company_data["company"].partner_id.write(
            {
                "country_id": cls.env.ref("base.br").id,
                "state_id": cls.env.ref("base.state_br_sp").id,
            }
        )

        cls.env.user.group_ids |= cls.env.ref("l10n_br_fiscal.group_manager")

        Pricelist = cls.env["product.pricelist"]
        PricelistItem = cls.env["product.pricelist.item"]
        # The Brazilian fiscal fields of the sale order form are only visible
        # when the form company is a Brazilian company: create the order in
        # the Brazilian test company instead of the main company of the user.
        SaleOrder = cls.env["sale.order"].with_context(
            tracking_disable=True,
            allowed_company_ids=cls.company_data["company"].ids,
        )

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

        # prices after product change.
        price_after = self.sale_order.order_line[0].price_unit
        fiscal_price_after = self.sale_order.order_line[0].fiscal_price

        # check if prices are the same.
        self.assertEqual(price_before, price_after)
        self.assertEqual(fiscal_price_before, fiscal_price_after)
