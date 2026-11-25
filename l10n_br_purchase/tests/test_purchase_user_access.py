# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestPurchaseUserAccess(TransactionCase):
    """A buyer without the fiscal group works with Brazilian purchase orders."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.partner = cls.env.ref("l10n_br_base.res_partner_akretion")
        cls.product = cls.env.ref("product.product_product_27")
        cls.fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.fiscal_operation_line = cls.env.ref("l10n_br_fiscal.fo_compras_compras")
        cls.buyer = new_test_user(
            cls.env,
            login="l10n_br_purchase_buyer",
            groups="purchase.group_purchase_user",
            company_id=cls.company.id,
        )
        cls.buyer.company_ids += cls.company
        cls.buyer_env = cls.env(
            user=cls.buyer,
            context=dict(
                cls.env.context,
                allowed_company_ids=cls.company.ids,
                default_company_id=cls.company.id,
            ),
        )

    def _order_vals(self):
        return {
            "partner_id": self.partner.id,
            "company_id": self.company.id,
            "fiscal_operation_id": self.fiscal_operation.id,
            "order_line": [
                Command.create(
                    {
                        "product_id": self.product.id,
                        "name": self.product.display_name,
                        "fiscal_operation_id": self.fiscal_operation.id,
                        "fiscal_operation_line_id": self.fiscal_operation_line.id,
                        "product_qty": 2,
                        "price_unit": 100,
                    }
                )
            ],
        }

    def _screen_fields(self, view_type):
        """Fields the web client asks for when it opens the order views.

        ``get_views`` already drops what the groups of the buyer hide, and
        lists the fields of the embedded line views under the line model.
        """
        env = self.buyer_env
        models = env["purchase.order"].get_views([(False, view_type)])["models"]
        return {
            model: [name for name in names if name in env[model]._fields]
            for model, names in models.items()
            if model in ("purchase.order", "purchase.order.line")
        }

    def test_buyer_creates_order_with_taxes(self):
        """The buyer saves an order with a line and the taxes are computed."""
        self.assertFalse(self.buyer.has_group("l10n_br_fiscal.group_user"))
        order = self.buyer_env["purchase.order"].create(self._order_vals())
        order_line = order.order_line
        self.assertTrue(order_line.fiscal_operation_line_id)
        self.assertTrue(order_line.fiscal_tax_ids)

    def test_buyer_opens_order_screens(self):
        """The buyer reads what the order form and list ask for, field by field."""
        env = self.buyer_env
        order = env["purchase.order"].create(self._order_vals())
        refused = {}
        for view_type in ("form", "tree"):
            screen = self._screen_fields(view_type)
            self.assertTrue(screen["purchase.order"])
            for model, names in screen.items():
                records = order if model == "purchase.order" else order.order_line
                for name in names:
                    # A new request starts with an empty cache, and a field
                    # must not profit from what another one has loaded.
                    env.invalidate_all()
                    try:
                        records.read([name])
                    except AccessError as err:
                        refused[(model, name)] = str(err)
        self.assertFalse(refused, "The buyer cannot read: %s" % sorted(refused))

    def test_buyer_edits_and_confirms_order(self):
        """The buyer fires the fiscal onchanges of the line, saves and confirms."""
        env = self.buyer_env
        screen = self._screen_fields("form")
        order_vals = self._order_vals()
        order_vals.pop("order_line")
        order = env["purchase.order"].create(order_vals)
        line_spec = {name: {} for name in screen["purchase.order.line"]}
        line_vals = {
            "order_id": order.id,
            "product_id": self.product.id,
            "fiscal_operation_id": self.fiscal_operation.id,
            "fiscal_operation_line_id": self.fiscal_operation_line.id,
            "product_qty": 2,
            "price_unit": 100,
        }
        for field_name in ("product_id", "fiscal_operation_line_id", "product_qty"):
            env["purchase.order.line"].onchange(line_vals, [field_name], line_spec)
        order.write({"order_line": self._order_vals()["order_line"]})
        order.order_line.write({"product_qty": 3})
        order.button_confirm()
        self.assertIn(order.state, ("purchase", "to approve"))
