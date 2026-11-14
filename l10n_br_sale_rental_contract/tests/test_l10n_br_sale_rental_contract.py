# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestL10nBrSaleRentalContract(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env.user.company_ids |= cls.company
        cls.env.user.company_id = cls.company
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=[cls.company.id])
        )
        cls.fo_locacao = cls.env.ref("l10n_br_fiscal.fo_locacao")
        (
            cls.env.ref("sale_rental.route_warehouse0_rental")
            | cls.env.ref("sale_rental.route_warehouse0_sell_rented_product")
        ).company_id = False
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id)], limit=1
        )
        cls.warehouse.rental_allowed = True
        cls.partner = cls.env.ref("l10n_br_base.res_partner_cliente1_sp")
        cls.partner.ind_ie_dest = "9"
        printer = cls.env["product.product"].create(
            {"name": "Impressora de produção", "detailed_type": "product"}
        )
        cls.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "product_id": printer.id,
                "location_id": cls.warehouse.rental_in_location_id.id,
                "inventory_quantity": 5,
            }
        )._apply_inventory()
        wizard = (
            cls.env["create.rental.product"]
            .with_context(active_model="product.product", active_id=printer.id)
            .create(
                {
                    "sale_price_per_day": 816.67,
                    "categ_id": cls.env.ref("product.product_category_all").id,
                }
            )
        )
        cls.rental_service = cls.env["product.product"].browse(
            wizard.create_rental_product()["res_id"]
        )
        template = cls.env["contract.template"].create(
            {"name": "Locação mensal", "contract_type": "sale"}
        )
        cls.rental_service.product_tmpl_id.with_company(cls.company).write(
            {
                "is_contract": True,
                "recurring_rule_type": "monthly",
                "recurring_invoicing_type": "pre-paid",
                "property_contract_template_id": template.id,
                "rental_contract_price": 24500.0,
            }
        )
        # starts today: the contract line is due now
        start = fields.Date.today()
        end = start + relativedelta(years=1, days=-1)
        days = (end - start).days + 1
        cls.order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "company_id": cls.company.id,
                "warehouse_id": cls.warehouse.id,
                "fiscal_operation_id": cls.env.ref("l10n_br_fiscal.fo_venda").id,
                "default_start_date": start,
                "default_end_date": end,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.rental_service.id,
                            "rental_type": "new_rental",
                            "rental_qty": 2,
                            "start_date": start,
                            "end_date": end,
                            "number_of_days": days,
                            "product_uom_qty": 2 * days,
                            "price_unit": 816.67,
                        },
                    )
                ],
            }
        )
        cls.order.action_confirm()
        cls.contract = cls.order.order_line.contract_id

    def test_rental_contract(self):
        self.assertEqual(self.contract.fiscal_operation_id, self.fo_locacao)
        line = self.contract.contract_line_ids
        self.assertEqual(line.fiscal_operation_id, self.fo_locacao)
        self.assertEqual(line.quantity, 2)
        self.assertEqual(line.price_unit, 24500.0)

    def test_monthly_rental_invoice(self):
        invoice = self.contract.recurring_create_invoice()
        self.assertEqual(invoice.fiscal_operation_id, self.fo_locacao)
        self.assertEqual(invoice.document_type_id.code, "SE")
        self.assertAlmostEqual(invoice.amount_untaxed, 49000.0)
        invoice_line = invoice.invoice_line_ids
        self.assertEqual(invoice_line.quantity, 2)
        self.assertFalse(invoice_line.issqn_value)
        self.assertEqual(invoice_line.tax_classification_id.code, "000001")
