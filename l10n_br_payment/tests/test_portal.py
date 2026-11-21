# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta
from unittest import SkipTest

from odoo import fields
from odoo.tests.common import HttpCase, tagged

# A valid Banco do Brasil digitable line (homologation set), and its grouping.
LINE = "00190000090312855720894786922172216610000025295"
LINE_SHOWN = "00190.00009 03128.557208 94786.922172 2 16610000025295"


@tagged("post_install", "-at_install")
class TestBoletoPortal(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        if not cls.env.company.chart_template:
            raise SkipTest("The test company needs a chart of accounts.")
        cls.provider = cls.env["payment.provider"].create(
            {"name": "Boleto test", "code": "none", "state": "test"}
        )
        term = cls.env["account.payment.term"].create(
            {
                "name": "3x",
                "line_ids": [
                    (0, 0, {"value": "percent", "value_amount": 30.0, "nb_days": 0}),
                    (0, 0, {"value": "percent", "value_amount": 30.0, "nb_days": 30}),
                    (0, 0, {"value": "percent", "value_amount": 40.0, "nb_days": 60}),
                ],
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {"name": "Portal Customer", "tz": "America/Sao_Paulo"}
        )
        cls.invoice = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.partner.id,
                "invoice_payment_term_id": term.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Service",
                            "quantity": 1,
                            "price_unit": 300.0,
                            "tax_ids": [(6, 0, [])],
                        },
                    )
                ],
            }
        )
        cls.invoice.action_post()
        cls.installments = cls.invoice.due_line_ids.sorted("date_maturity")
        cls.txs = cls.env["payment.transaction"]
        for number, installment in enumerate(cls.installments, start=1):
            cls.txs |= cls.env["payment.transaction"].create(
                {
                    "reference": f"portal-{number}",
                    "provider_id": cls.provider.id,
                    "amount": installment.amount_residual,
                    "currency_id": cls.invoice.currency_id.id,
                    "partner_id": cls.partner.id,
                    "payment_method_id": cls.env.ref(
                        "payment.payment_method_boleto"
                    ).id,
                    "operation": "offline",
                    "is_boleto_payment": True,
                    "due_date": installment.date_maturity,
                    "move_line_id": installment.id,
                    "invoice_ids": [(6, 0, cls.invoice.ids)],
                    "digitable_line": LINE,
                    "pix_copia_cola": f"00020101PIX{number}",
                    "state": "pending",
                }
            )

    def test_digitable_line_display(self):
        tx = self.txs[0]
        self.assertEqual(tx._boleto_digitable_line_display(), LINE_SHOWN)
        tx.digitable_line = "8" * 48
        self.assertEqual(
            tx._boleto_digitable_line_display(),
            " ".join(["8" * 12] * 4),
        )
        tx.digitable_line = "123"
        self.assertEqual(tx._boleto_digitable_line_display(), "123")

    def test_overdue_counts_the_payer_day(self):
        tx = self.txs[0]
        today = fields.Date.context_today(tx.with_context(tz="America/Sao_Paulo"))
        tx.due_date = today
        self.assertFalse(tx._boleto_is_overdue())
        tx.due_date = today - timedelta(days=1)
        self.assertTrue(tx._boleto_is_overdue())
        tx.state = "done"
        self.assertFalse(tx._boleto_is_overdue())

    def test_portal_lists_every_installment(self):
        self.txs[0].state = "done"
        url = (
            f"/my/invoices/{self.invoice.id}"
            f"?access_token={self.invoice._portal_ensure_token()}"
        )
        response = self.url_open(url)
        self.assertEqual(response.status_code, 200)
        page = response.text
        # The sidebar header keeps the invoice amount, not the loop record.
        self.assertNotIn("payment.transaction(", page)
        self.assertIn("boleto_titles", page)
        # Numbered in the whole invoice: the paid first one still counts, so the
        # next to pay is the second of three (any language: "of", "de").
        self.assertRegex(page, r"\b2\s+\w+\s+3\b")
        # The paid installment shows no codes; the open ones do.
        self.assertNotIn("00020101PIX1", page)
        self.assertIn("00020101PIX2", page)
        self.assertIn("00020101PIX3", page)
        self.assertIn(LINE_SHOWN, page)
        # Only the next installment comes expanded.
        self.assertEqual(page.count('<details class="card o_boleto_title" open'), 1)
