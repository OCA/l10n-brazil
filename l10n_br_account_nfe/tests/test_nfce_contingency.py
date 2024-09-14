# Copyright 2023 KMEE (Felipe Zago Rodrigues <felipe.zago@kmee.com.br>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase


class TestAccountNFCeContingency(TransactionCase):
    def setUp(self):
        super().setUp()
        # this hook is required to test l10n_br_account_nfe alone:
        self.env["spec.mixin.nfe"]._register_hook()
        self.document_id = self.env.ref("l10n_br_nfe.demo_nfce_same_state")
        self.prepare_account_move_nfce()

    def prepare_account_move_nfce(self):
        receivable_account_id = self.env["account.account"].create(
            {
                "name": "TEST ACCOUNT",
                "code": "1.1.1.2.2",
                "reconcile": 1,
                "company_id": self.env.ref("base.main_company").id,
                "user_type_id": self.env.ref("account.data_account_type_receivable").id,
            }
        )
        payable_account_id = self.env["account.account"].create(
            {
                "name": "TEST ACCOUNT 2",
                "code": "1.1.1.2.3",
                "reconcile": 1,
                "company_id": self.env.ref("base.main_company").id,
                "user_type_id": self.env.ref("account.data_account_type_payable").id,
            }
        )
        payment_method = self.env.ref("account.account_payment_method_manual_in").id
        journal_id = self.env["account.journal"].create(
            {
                "name": "JOURNAL TEST",
                "code": "TEST",
                "type": "bank",
                "company_id": self.env.ref("base.main_company").id,
            }
        )
        payment_mode = self.env["account.payment.mode"].create(
            {
                "name": "PAYMENT MODE TEST",
                "company_id": self.env.ref("base.main_company").id,
                "payment_method_id": payment_method,
                "fiscal_payment_mode": "15",
                "bank_account_link": "fixed",
                "fixed_journal_id": journal_id.id,
            }
        )
        self.document_move_id = self.env["account.move"].create(
            {
                "name": "MOVE TEST",
                "payment_mode_id": payment_mode.id,
                "company_id": self.env.ref("base.main_company").id,
                "line_ids": [
                    (0, 0, {"account_id": receivable_account_id.id, "credit": 10}),
                    (0, 0, {"account_id": payable_account_id.id, "debit": 10}),
                ],
            }
        )
        self.document_move_id.fiscal_document_id = self.document_id.id

    def test_nfce_contingencia(self):
        self.document_id._update_nfce_for_offline_contingency()
        self.assertIn(self.document_move_id, self.document_id.move_ids)
