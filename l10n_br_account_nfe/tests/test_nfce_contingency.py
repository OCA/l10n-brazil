# Copyright 2023 KMEE (Felipe Zago Rodrigues <felipe.zago@kmee.com.br>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.tests import tagged

from odoo.addons.l10n_br_account.tests.common import AccountMoveBRCommon

from .tools import load_account_nfe_fixture_files


@tagged("post_install", "-at_install")
class TestAccountNFCeContingency(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Add required groups BEFORE accessing e-doc data
        cls.env.user.groups_id |= cls.env.ref("l10n_br_nfe.group_manager")
        cls.env.user.groups_id |= cls.env.ref("l10n_br_fiscal.group_manager")
        cls.env.user.groups_id |= cls.env.ref("account.group_account_manager")

        # Grant access to all companies (demo data belongs to different companies)
        companies = cls.env["res.company"].search([])
        cls.env.user.company_ids = [Command.set(companies.ids)]

        if not cls.env.ref(
            "l10n_br_nfe.demo_nfce_same_state", raise_if_not_found=False
        ):
            load_account_nfe_fixture_files(cls.env)

        cls.document_id = cls.env.ref("l10n_br_nfe.demo_nfce_same_state")

        # Create a fake certificate so the EDI workflow doesn't fail
        # (same pattern as l10n_br_nfe tests)
        from erpbrasil.assinatura import misc

        certificate_valid = misc.create_fake_certificate_file(
            valid=True,
            passwd="123456",
            issuer="EMISSOR A TESTE",
            country="BR",
            subject="CERTIFICADO VALIDO TESTE",
        )
        certificate_id = cls.env["l10n_br_fiscal.certificate"].create(
            {
                "type": "nf-e",
                "subtype": "a1",
                "password": "123456",
                "file": certificate_valid,
            }
        )
        cls.document_id.company_id.certificate_nfe_id = certificate_id
        cls.document_id.company_id.nfce_csc_token = "DUMMY"
        cls.document_id.company_id.nfce_csc_code = "DUMMY"

        cls.prepare_account_move_nfce()

    @classmethod
    def prepare_account_move_nfce(cls):
        company = cls.company_data["company"]
        receivable_account_id = cls.env["account.account"].create(
            {
                "name": "TEST ACCOUNT",
                "code": "01.1.1.2.2",
                "reconcile": 1,
                "account_type": "asset_receivable",
            }
        )
        payable_account_id = cls.env["account.account"].create(
            {
                "name": "TEST ACCOUNT 2",
                "code": "01.1.1.2.3",
                "reconcile": 1,
                "account_type": "liability_payable",
            }
        )
        payment_method = cls.env.ref("account.account_payment_method_manual_in").id
        journal_id = cls.env["account.journal"].create(
            {
                "name": "JOURNAL TEST",
                "code": "TEST",
                "type": "bank",
            }
        )
        payment_mode = cls.env["account.payment.mode"].create(
            {
                "name": "PAYMENT MODE TEST",
                "company_id": company.id,
                "payment_method_id": payment_method,
                "fiscal_payment_mode": "15",
                "bank_account_link": "fixed",
                "fixed_journal_id": journal_id.id,
            }
        )
        # Use create directly for simple entry move
        # (Form triggers l10n_br_account tax computation even for entries)
        cls.document_move_id = (
            cls.env["account.move"]
            .sudo()
            .create(
                {
                    "name": "MOVE TEST",
                    "move_type": "entry",
                    "journal_id": journal_id.id,
                    "payment_mode_id": payment_mode.id,
                    "company_id": company.id,
                    "line_ids": [
                        Command.create(
                            {"account_id": receivable_account_id.id, "credit": 10}
                        ),
                        Command.create(
                            {"account_id": payable_account_id.id, "debit": 10}
                        ),
                    ],
                }
            )
        )
        cls.document_move_id.fiscal_document_id = cls.document_id.id

    def test_nfce_contingencia(self):
        self.document_id._update_nfce_for_offline_contingency()
        self.assertIn(self.document_move_id, self.document_id.move_ids)
