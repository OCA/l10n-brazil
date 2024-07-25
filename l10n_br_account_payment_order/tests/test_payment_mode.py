# @ 2021 KMEE - kmee.com.br
#   Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import unittest

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase


class TestPaymentMode(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        if not cls.env["account.account"].search([]):
            raise unittest.SkipTest("No accounts defined")

        cls.company = cls.env.ref("base.main_company")
        cls.journal_c1 = cls.env["account.journal"].create(
            {
                "name": "Journal 1",
                "code": "J1",
                "type": "bank",
                "company_id": cls.company.id,
            }
        )

        cls.account = cls.env["account.account"].search(
            [("reconcile", "=", True), ("company_id", "=", cls.company.id)], limit=1
        )

        cls.type_240 = cls.env.ref(
            "l10n_br_account_payment_order.payment_mode_type_cnab240"
        )

        cls.type_400 = cls.env.ref(
            "l10n_br_account_payment_order.payment_mode_type_cnab400"
        )

        cls.type_500 = cls.env.ref(
            "l10n_br_account_payment_order.payment_mode_type_cnab500"
        )

        cls.payment_mode_test_240 = cls.env["account.payment.mode"].create(
            {
                "name": "Banco Teste 240",
                "bank_account_link": "fixed",
                "payment_method_id": cls.type_240.id,
                "company_id": cls.company.id,
                "fixed_journal_id": cls.journal_c1.id,
                "group_lines": False,
            }
        )

        cls.payment_mode_test_400 = cls.env["account.payment.mode"].create(
            {
                "name": "Banco Teste 400",
                "bank_account_link": "fixed",
                "payment_method_id": cls.type_400.id,
                "company_id": cls.company.id,
                "fixed_journal_id": cls.journal_c1.id,
                "group_lines": False,
            }
        )

        cls.payment_mode_test_500 = cls.env["account.payment.mode"].create(
            {
                "name": "Banco Teste 500",
                "bank_account_link": "fixed",
                "payment_method_id": cls.type_500.id,
                "company_id": cls.company.id,
                "fixed_journal_id": cls.journal_c1.id,
                "group_lines": False,
            }
        )

    def test_onchange(self):
        """Test account.payment.mode Onchange methods"""
        self.payment_mode_test_240._onchange_payment_method_id()

    def test_constrains(self):
        """Test account.payment.mode Constrains methods"""
        with self.assertRaises(ValidationError):
            self.payment_mode_test_240.write(
                {
                    "group_lines": True,
                }
            )
