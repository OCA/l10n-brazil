from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged

GENERATE = (
    "odoo.addons.l10n_br_payment.models.account_move.AccountMove.generate_boletos"
)


@tagged("post_install", "-at_install")
class TestL10nBrPaymentBoleto(TransactionCase):
    def setUp(self):
        super().setUp()
        self.payment_provider = self.env["payment.provider"].create(
            {"name": "Test Payment Provider", "code": "none", "state": "enabled"}
        )
        journal = self.env["account.journal"].search(
            [
                ("type", "in", ("bank", "cash")),
                ("company_id", "=", self.env.company.id),
            ],
            limit=1,
        )
        self.payment_mode = self.env["account.payment.mode"].create(
            {
                "name": "Test Payment Mode",
                "bank_account_link": "fixed",
                "fixed_journal_id": journal.id,
                "generate_boletos_on_invoice": True,
                "payment_provider_id": self.payment_provider.id,
                "payment_method_id": self.env.ref(
                    "account.account_payment_method_manual_in"
                ).id,
            }
        )
        self.account_move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.env.ref("base.res_partner_1").id,
                "invoice_date": "2023-01-01",
                "invoice_line_ids": [
                    (0, 0, {"name": "Test Product", "quantity": 1, "price_unit": 100})
                ],
                "payment_mode_id": self.payment_mode.id,
            }
        )

    def test_generate_boletos_on_invoice_flag(self):
        with patch(GENERATE) as generate:
            self.account_move.action_post()
            generate.assert_called_once()
        self.payment_mode.generate_boletos_on_invoice = False
        with patch(GENERATE) as generate:
            self.account_move.copy().action_post()
            generate.assert_not_called()

    def test_generate_boletos_of_several_invoices(self):
        moves = self.account_move | self.account_move.copy()
        with patch(GENERATE) as generate:
            moves.action_post()
            self.assertEqual(generate.call_count, 2)

    def test_generate_boletos_without_provider(self):
        self.payment_mode.payment_provider_id = False
        with self.assertRaises(UserError):
            self.account_move.action_post()
