# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import Form, TransactionCase, tagged

from odoo.addons.l10n_br_fiscal.tests.tools import load_fiscal_fixture_files


@tagged("post_install", "-at_install")
class TestSaleSalesmanAccess(TransactionCase):
    """A user with only the Sales salesman access must be able to open and
    create sale orders with Brazilian fiscal lines."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_fiscal_fixture_files(cls.env)
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                tracking_disable=True,
                allowed_company_ids=cls.company.ids,
            )
        )
        cls.env.user.company_ids += cls.company
        cls.env.user.company_id = cls.company
        cls.fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.partner = cls.env.ref("l10n_br_base.res_partner_akretion")
        cls.product = cls.env.ref("product.product_product_27")
        cls.salesman = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Salesman Own Documents",
                    "login": "l10n_br_sale_salesman",
                    "email": "salesman@example.com",
                    "company_id": cls.company.id,
                    "company_ids": [Command.set(cls.company.ids)],
                    "groups_id": [
                        Command.set([cls.env.ref("sales_team.group_sale_salesman").id])
                    ],
                }
            )
        )
        order_form = Form(
            cls.env["sale.order"].with_context(default_company_id=cls.company.id)
        )
        order_form.partner_id = cls.partner
        order_form.user_id = cls.salesman
        order_form.fiscal_operation_id = cls.fiscal_operation
        with order_form.order_line.new() as line:
            line.product_id = cls.product
            line.product_uom_qty = 2
            line.price_unit = 500
        cls.order = order_form.save()

    def _read_like_web_client(self, records):
        """Read the records with the fields of their form view, as the web
        client does, including the display name of the related records."""
        views = records.get_views([(False, "form")])
        models_fields = views["models"]
        for model_name in (records._name, "sale.order.line"):
            fields_info = models_fields.get(model_name, {}).get("fields", {})
            model_records = (
                records if model_name == records._name else records.order_line
            )
            model_records.read(list(fields_info))
            for fname, descr in fields_info.items():
                if descr["type"] in ("many2one", "many2many"):
                    model_records.mapped(fname).read(["display_name"])

    def test_salesman_open_sale_order(self):
        """The salesman opens his quotation with a fiscal line."""
        self.assertTrue(self.order.order_line.fiscal_tax_ids)
        order = self.order.with_user(self.salesman)
        self._read_like_web_client(order)
        order_form = Form(order)
        self.assertEqual(len(order_form.order_line), 1)

    def test_salesman_create_sale_order(self):
        """The salesman creates a quotation and the fiscal data is computed."""
        order_form = Form(
            self.env["sale.order"]
            .with_user(self.salesman)
            .with_context(default_company_id=self.company.id)
        )
        order_form.partner_id = self.partner
        order_form.fiscal_operation_id = self.fiscal_operation
        with order_form.order_line.new() as line:
            line.product_id = self.product
            line.product_uom_qty = 1
            line.price_unit = 100
        order = order_form.save()
        self.assertEqual(order.user_id, self.salesman)
        self.assertTrue(order.order_line.fiscal_tax_ids)
        self._read_like_web_client(order)
