# Copyright (C) 2022 - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import fields
from odoo.tests.common import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestReturnLog(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(
        cls, chart_template_ref="l10n_br_coa_generic.l10n_br_coa_generic_template"
    ):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.event_obj = cls.env["l10n_br_cnab.return.event"]
        cls.return_log_obj = cls.env["l10n_br_cnab.return.log"]
        cls.res_partner_obj = cls.env["res.partner.bank"]
        cls.inv_line_obj = cls.env["account.move.line"]
        cls.bank_341 = cls.env.ref("l10n_br_base.res_bank_341")
        cls.company = cls.company_data["company"]
        cls.brl_currency = cls.env.ref("base.BRL")
        cls.rebate_account = cls.env["account.account"].create(
            {
                "company_id": cls.company.id,
                "code": "TEST1",
                "name": "Rebate Account",
                "account_type": "expense",
                "reconcile": False,
            }
        )
        cls.discount_account = cls.env["account.account"].create(
            {
                "company_id": cls.company.id,
                "code": "TEST2",
                "name": "Discount Account",
                "account_type": "expense",
                "reconcile": False,
            }
        )
        cls.tariff_account = cls.env["account.account"].create(
            {
                "company_id": cls.company.id,
                "code": "TEST3",
                "name": "Tariff Account",
                "account_type": "expense",
                "reconcile": False,
            }
        )
        cls.itau_bank_account = cls.res_partner_obj.create(
            {
                "acc_number": "205040",
                "bra_number": "1030",
                "bank_id": cls.bank_341.id,
                "company_id": cls.company.id,
                "partner_id": cls.company.partner_id.id,
            }
        )
        cls.bank_journal_itau = cls.env["account.journal"].create(
            {
                "name": "Itau Bank",
                "type": "bank",
                "code": "BNK_ITAU",
                "bank_account_id": cls.itau_bank_account.id,
                "bank_id": cls.bank_341.id,
                "currency_id": cls.brl_currency.id,
                "inbound_rebate_account_id": cls.rebate_account.id,
                "inbound_discount_account_id": cls.discount_account.id,
                "tariff_charge_account_id": cls.tariff_account.id,
            }
        )
        cls.invoice = cls.env["account.move"].create(
            {
                "partner_id": cls.partner_a.id,
                "move_type": "out_invoice",
                "ref": "Test Customer Invoice 1",
                "invoice_date": fields.Date.today(),
                "company_id": cls.company.id,
                "journal_id": cls.company_data["default_journal_sale"].id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product_a.id,
                            "quantity": 1.0,
                            "price_unit": 200.0,
                        },
                    )
                ],
            }
        )

    def test_move_create(self):
        self.invoice.action_post()
        return_log = self.return_log_obj.create(
            {
                "journal_id": self.bank_journal_itau.id,
                "type": "inbound",
            }
        )
        move_line_ids = self.invoice.line_ids.filtered(
            lambda line: line.account_type == "asset_receivable"
        )
        event = self.event_obj.create(
            {
                "discount_value": 10.00,
                "rebate_value": 2.00,
                "gen_liquidation_move": True,
                "payment_value": 188.00,
                "tariff_charge": 5.00,
                "real_payment_date": date(2023, 4, 1),
                "cnab_return_log_id": return_log.id,
                "move_line_ids": move_line_ids,
                "your_number": "ABCX123",
            }
        )
        event.confirm_event()
        receivable_moves = event.generated_move_id.line_ids.filtered(
            lambda line: line.account_type == "asset_receivable"
        )
        bank_moves = event.generated_move_id.line_ids.filtered(
            lambda line: line.account_id
            in (
                self.bank_journal_itau.default_account_id,
                self.bank_journal_itau.company_id.account_journal_payment_debit_account_id,
                self.bank_journal_itau.company_id.account_journal_payment_credit_account_id,
            )
        )
        rebate_moves = event.generated_move_id.line_ids.filtered(
            lambda line: line.account_id == self.rebate_account
        )
        discount_moves = event.generated_move_id.line_ids.filtered(
            lambda line: line.account_id == self.discount_account
        )
        tariff_moves = event.generated_move_id.line_ids.filtered(
            lambda line: line.account_id == self.tariff_account
        )

        def sum_balance(moves_lines):
            return sum(moves_lines.mapped("balance"))

        self.assertEqual(sum_balance(receivable_moves), -200.00)
        self.assertEqual(sum_balance(bank_moves), 183.00)
        self.assertEqual(sum_balance(rebate_moves), 2.00)
        self.assertEqual(sum_balance(discount_moves), 10.00)
        self.assertEqual(sum_balance(tariff_moves), 5.00)
