# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import Form, TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestPurchaseUserAccess(TransactionCase):
    """A buyer without the fiscal group can create a Brazilian purchase order."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.partner = cls.env.ref("l10n_br_base.res_partner_akretion")
        cls.product = cls.env.ref("product.product_product_27")
        cls.fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.buyer = new_test_user(
            cls.env,
            login="l10n_br_purchase_buyer",
            groups="purchase.group_purchase_user",
            company_id=cls.company.id,
        )
        cls.buyer.company_ids += cls.company

    def test_buyer_creates_order_with_taxes(self):
        """The buyer saves an order with a line and the taxes are computed."""
        self.assertFalse(self.buyer.has_group("l10n_br_fiscal.group_user"))
        env = self.env(
            user=self.buyer,
            context=dict(
                self.env.context,
                allowed_company_ids=self.company.ids,
                default_company_id=self.company.id,
            ),
        )
        order_form = Form(env["purchase.order"])
        order_form.partner_id = env["res.partner"].browse(self.partner.id)
        order_form.fiscal_operation_id = env["l10n_br_fiscal.operation"].browse(
            self.fiscal_operation.id
        )
        with order_form.order_line.new() as line:
            line.product_id = env["product.product"].browse(self.product.id)
            line.product_qty = 2
            line.price_unit = 100
        order = order_form.save()
        order_line = order.order_line
        self.assertTrue(order_line.fiscal_operation_line_id)
        self.assertTrue(order_line.fiscal_tax_ids)
        self.assertTrue(order_line.icms_tax_id or order_line.pis_tax_id)
