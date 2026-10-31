# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest import SkipTest

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestBoletoInstallmentReconcile(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        company = cls.env.company
        if not company.chart_template_id:
            raise SkipTest("The test company needs a chart of accounts.")
        journal = cls.env["account.journal"].search(
            [("type", "=", "bank"), ("company_id", "=", company.id)], limit=1
        )
        cls.method_line = journal.inbound_payment_method_line_ids[:1]
        cls.provider = cls.env["payment.provider"].create(
            {"name": "Boleto test", "code": "none", "state": "test"}
        )
        term = cls.env["account.payment.term"].create(
            {
                "name": "30/60",
                "line_ids": [
                    (0, 0, {"value": "percent", "value_amount": 50.0, "days": 30}),
                    (0, 0, {"value": "balance", "value_amount": 0.0, "days": 60}),
                ],
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Installment Customer"})
        cls.invoice = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.partner.id,
                "invoice_date": "2026-01-05",
                "invoice_payment_term_id": term.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Service",
                            "quantity": 1,
                            "price_unit": 200.0,
                            "tax_ids": [(6, 0, [])],
                        },
                    )
                ],
            }
        )
        cls.invoice.action_post()
        cls.first, cls.second = cls.invoice.due_line_ids.sorted("date_maturity")

    def _transaction(self, installment, reference, **values):
        return self.env["payment.transaction"].create(
            {
                "reference": reference,
                "provider_id": self.provider.id,
                "amount": installment.amount_residual,
                "currency_id": self.invoice.currency_id.id,
                "partner_id": self.partner.id,
                "is_boleto_payment": True,
                "due_date": installment.date_maturity,
                "invoice_ids": [(6, 0, self.invoice.ids)],
                **values,
            }
        )

    def _pay(self, tx):
        tx._set_done()
        return tx._create_payment(payment_method_line_id=self.method_line.id)

    def test_out_of_order_payment_settles_its_own_installment(self):
        tx = self._transaction(self.second, "out-of-order", move_line_id=self.second.id)
        self._pay(tx)
        self.assertTrue(self.second.reconciled)
        self.assertFalse(self.first.reconciled)

    def test_core_behaviour_without_installment(self):
        self._pay(self._transaction(self.first, "no-installment"))
        self.assertTrue(self.first.reconciled)
        self.assertFalse(self.second.reconciled)

    def test_installment_paid_with_interest_keeps_the_rest_open(self):
        tx = self._transaction(
            self.first, "interest", move_line_id=self.first.id, amount=103.0
        )
        payment = self._pay(tx)
        self.assertTrue(self.first.reconciled)
        self.assertEqual(self.second.amount_residual, 100.0)
        counterpart = payment.line_ids.filtered(
            lambda line: line.account_id == payment.destination_account_id
        )
        self.assertEqual(counterpart.amount_residual, -3.0)

    def test_active_and_report_transactions(self):
        self.assertFalse(self.invoice._boleto_get_active_transactions(self.first))
        tx = self._transaction(self.first, "active", move_line_id=self.first.id)
        self.assertEqual(self.invoice._boleto_get_active_transactions(self.first), tx)
        self.assertFalse(self.invoice._boleto_get_active_transactions(self.second))
        self.assertFalse(self.invoice._boleto_report_transactions())
        tx.write({"pix_copia_cola": "00020101", "state": "pending"})
        self.assertEqual(self.invoice._boleto_report_transactions(), tx)
        tx._set_error("refused")
        self.assertFalse(self.invoice._boleto_get_active_transactions(self.first))
        self.assertFalse(self.invoice._boleto_report_transactions())
