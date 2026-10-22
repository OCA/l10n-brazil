# Copyright 2022 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests import TransactionCase


class L10nBrSaleInvoicePlanBaseTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.so_service = cls.env.ref(
            "l10n_br_sale_invoice_plan.lc_so_invoice_plan_service_br"
        )
        cls.sl_service_1 = cls.env.ref(
            "l10n_br_sale_invoice_plan.lc_sl_invoice_plan_service_br_1_1"
        )

        cls.fsc_op_sale = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.fsc_op_line_serv = cls.env.ref("l10n_br_fiscal.fo_venda_servico")

    def test_l10n_br_sale_invoice_plan_service(self):
        ctx = {
            "active_id": self.so_service.id,
            "active_ids": [self.so_service.id],
            "all_remain_invoices": False,
            "default_company_id": self.company.id,
            "allowed_company_ids": self.company.ids,
        }
        self.so_service.action_confirm()
        make_wizard = self.env["sale.make.planned.invoice"].create({})
        make_wizard.with_context(**ctx).create_invoices_by_plan()
        invoices = self.so_service.invoice_ids
        line = invoices[0].invoice_line_ids[0]
        self.assertEqual(len(invoices), 1, "Only 1 invoice should be created")
        self.assertEqual(
            line.quantity,
            line.fiscal_quantity,
            "The fiscal_quantity must be equal the quantity",
        )
        self.assertTrue(line.fiscal_operation_id)
        self.assertTrue(line.fiscal_tax_ids)
        self.assertTrue(line.tax_ids)


class L10nBrSaleInvoicePlanDownpaymentTest(TransactionCase):
    """The downpayment (sinal) is deducted from the amount to pay of the next
    invoices, while the fiscal document keeps the full value of the goods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env.user.company_ids |= cls.company
        cls.env.user.company_id = cls.company
        cls.advance_account = cls.env["account.account"].create(
            {
                "code": "2.1.9.9.99",
                "name": "Customer advances",
                "account_type": "liability_current",
                "company_id": cls.company.id,
            }
        )
        # The downpayment invoice is booked on the income account of the deposit
        # product: pointing it to a liability account makes it a customer advance.
        deposit = cls.env["product.product"].create(
            {
                "name": "Down payment",
                "type": "service",
                "invoice_policy": "order",
                "company_id": False,
                "property_account_income_id": cls.advance_account.id,
            }
        )
        cls.env["ir.config_parameter"].sudo().set_param(
            "sale.default_deposit_product_id", deposit.id
        )
        partner = cls.env.ref("l10n_br_base.res_partner_akretion")
        cls.order = (
            cls.env["sale.order"]
            .with_company(cls.company)
            .create(
                {
                    "partner_id": partner.id,
                    "partner_invoice_id": partner.id,
                    "partner_shipping_id": partner.id,
                    "company_id": cls.company.id,
                    "pricelist_id": cls.env.ref("product.list0").id,
                    "fiscal_operation_id": cls.env.ref("l10n_br_fiscal.fo_venda").id,
                    "use_invoice_plan": True,
                    "order_line": [
                        (
                            0,
                            0,
                            {
                                "name": "Service",
                                "product_id": cls.env.ref(
                                    "l10n_br_fiscal.customized_development_sale"
                                ).id,
                                "product_uom_qty": 10,
                                "product_uom": cls.env.ref("uom.product_uom_hour").id,
                                "price_unit": 1000.0,
                                "fiscal_operation_id": cls.env.ref(
                                    "l10n_br_fiscal.fo_venda"
                                ).id,
                                "fiscal_operation_line_id": cls.env.ref(
                                    "l10n_br_fiscal.fo_venda_servico"
                                ).id,
                            },
                        )
                    ],
                }
            )
        )
        today = fields.Date.today()
        cls.order.write(
            {
                "invoice_plan_ids": [
                    (
                        0,
                        0,
                        {
                            "installment": installment,
                            "plan_date": today,
                            "invoice_type": invoice_type,
                            "percent": percent,
                        },
                    )
                    for installment, invoice_type, percent in (
                        (0, "advance", 30.0),
                        (1, "installment", 40.0),
                        (2, "installment", 60.0),
                    )
                ]
            }
        )

    def _make_next_invoice(self):
        # to_invoice is computed without depends, so the cache must be dropped
        # between two invoices
        self.order.invoice_plan_ids.invalidate_recordset(["to_invoice"])
        ctx = {
            "active_id": self.order.id,
            "active_ids": self.order.ids,
            "all_remain_invoices": False,
            "default_company_id": self.company.id,
            "allowed_company_ids": self.company.ids,
        }
        self.env["sale.make.planned.invoice"].create({}).with_context(
            **ctx
        ).create_invoices_by_plan()

    def _receivable(self, move):
        return sum(
            move.line_ids.filtered(lambda ln: ln.display_type == "payment_term").mapped(
                "balance"
            )
        )

    def _advance_balance(self, move):
        return sum(
            move.line_ids.filtered(
                lambda ln: ln.account_id == self.advance_account
            ).mapped("balance")
        )

    def test_downpayment_is_deducted_from_next_invoices(self):
        self.order.action_confirm()
        for _i in range(3):
            self._make_next_invoice()
        advance, first, second = self.order.invoice_ids.sorted("id")

        # Amount to pay: 3,000 (downpayment), 4,000 - 40% of 3,000 and 6,000 - 60%
        # of 3,000. Together they are the 10,000 of the order.
        self.assertEqual(advance.amount_total, 3000.0)
        self.assertEqual(first.amount_total, 2800.0)
        self.assertEqual(second.amount_total, 4200.0)
        self.assertEqual(self._receivable(advance), 3000.0)
        self.assertEqual(self._receivable(first), 2800.0)
        self.assertEqual(self._receivable(second), 4200.0)
        self.assertEqual(first.amount_residual, 2800.0)
        self.assertEqual(second.amount_residual, 4200.0)
        self.assertEqual(
            sum(self.order.invoice_ids.mapped("amount_total")), self.order.amount_total
        )

        # The fiscal document keeps the full value of the goods
        self.assertFalse(advance.fiscal_document_id)
        self.assertEqual(first.fiscal_document_id.fiscal_amount_total, 4000.0)
        self.assertEqual(second.fiscal_document_id.fiscal_amount_total, 6000.0)
        self.assertEqual(len(first.fiscal_document_id.fiscal_line_ids), 1)
        self.assertEqual(len(second.fiscal_document_id.fiscal_line_ids), 1)

        # Accounting entries: the downpayment goes to the customer advance
        # account and each installment clears its part, so the advance is
        # fully consumed at the end.
        self.assertEqual(self._advance_balance(advance), -3000.0)
        self.assertEqual(self._advance_balance(first), 1200.0)
        self.assertEqual(self._advance_balance(second), 1800.0)
        for move in (advance, first, second):
            self.assertEqual(sum(move.line_ids.mapped("balance")), 0.0)
        # revenue keeps the full value of the goods: what is credited besides the
        # advance account is the goods (net of the taxes included in the price)
        # plus those taxes, i.e. 4,000 and 6,000
        for move, goods in ((first, 4000.0), (second, 6000.0)):
            credited = sum(
                ln.balance
                for ln in move.line_ids
                if ln.balance < 0 and ln.account_id != self.advance_account
            )
            self.assertAlmostEqual(credited, -goods, places=2)

    def test_downpayment_deduction_is_kept_after_posting(self):
        self.order.action_confirm()
        for _i in range(3):
            self._make_next_invoice()
        invoices = self.order.invoice_ids.sorted("id")
        invoices.action_post()
        self.assertEqual(
            invoices.mapped("amount_total"),
            [3000.0, 2800.0, 4200.0],
        )
        self.assertEqual(sum(invoices.mapped("amount_residual")), 10000.0)
