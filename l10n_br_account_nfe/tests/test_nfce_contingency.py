# Copyright 2023 KMEE (Felipe Zago Rodrigues <felipe.zago@kmee.com.br>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.tests import TransactionCase


class TestAccountNFCeContingency(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.document_id = cls.env.ref("l10n_br_nfe.demo_nfce_same_state")
        cls.prepare_account_move_nfce()

    @classmethod
    def prepare_account_move_nfce(cls):
        receivable_account_id = cls.env["account.account"].create(
            {
                "name": "TEST ACCOUNT",
                "code": "01.1.1.2.2",
                "reconcile": 1,
                "company_id": cls.env.ref("base.main_company").id,
                "account_type": "asset_receivable",
            }
        )
        payable_account_id = cls.env["account.account"].create(
            {
                "name": "TEST ACCOUNT 2",
                "code": "01.1.1.2.3",
                "reconcile": 1,
                "company_id": cls.env.ref("base.main_company").id,
                "account_type": "liability_payable",
            }
        )
        payment_method = cls.env.ref("account.account_payment_method_manual_in").id
        journal_id = cls.env["account.journal"].create(
            {
                "name": "JOURNAL TEST",
                "code": "TEST",
                "type": "bank",
                "company_id": cls.env.ref("base.main_company").id,
            }
        )
        payment_mode = cls.env["account.payment.mode"].create(
            {
                "name": "PAYMENT MODE TEST",
                "company_id": cls.env.ref("base.main_company").id,
                "payment_method_id": payment_method,
                "fiscal_payment_mode": "15",
                "bank_account_link": "fixed",
                "fixed_journal_id": journal_id.id,
            }
        )
        cls.document_move_id = cls.env["account.move"].create(
            {
                "name": "MOVE TEST",
                "payment_mode_id": payment_mode.id,
                "company_id": cls.env.ref("base.main_company").id,
                "line_ids": [
                    Command.create(
                        {"account_id": receivable_account_id.id, "credit": 10}
                    ),
                    Command.create({"account_id": payable_account_id.id, "debit": 10}),
                ],
            }
        )
        cls.document_move_id.fiscal_document_id = cls.document_id.id

    def test_nfce_contingencia(self):
        self.document_id._update_nfce_for_offline_contingency()
        self.assertIn(self.document_move_id, self.document_id.move_ids)
