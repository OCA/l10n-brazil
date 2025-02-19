# Copyright (C) 2021-Today - KMEE (<http://kmee.com.br>).
# @author Luis Felipe Mileo <mileo@kmee.com.br>
# Copyright (C) 2024-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo.tests import tagged

from .test_base_class import TestL10nBrAccountPaymentOder


@tagged("post_install", "-at_install")
class TestPaymentOrderChange(TestL10nBrAccountPaymentOder):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.invoice_auto = cls.env.ref(
            "l10n_br_account_payment_order." "demo_invoice_automatic_test"
        )
        if cls.invoice_auto.state == "draft":
            cls.invoice_auto.action_post()

        cls.financial_move_line_ids = cls.invoice_auto.financial_move_line_ids
        cls.financial_move_line_0 = cls.financial_move_line_ids[0]
        cls.financial_move_line_1 = cls.financial_move_line_ids[1]

        assert cls.financial_move_line_0, "Move 0 not created for open invoice"
        assert cls.financial_move_line_1, "Move 1 not created for open invoice"

        payment_order = cls.env["account.payment.order"].search(
            [
                ("state", "=", "draft"),
                ("payment_mode_id", "=", cls.invoice_auto.payment_mode_id.id),
            ]
        )
        cls._payment_order_all_workflow(cls, payment_order)

        # Testa o caso do raise UserError quando não há um Código para a Operação
        cls.invoice_manual = cls.env.ref(
            "l10n_br_account_payment_order." "demo_invoice_manual_test"
        )
        cls.invoice_manual.payment_mode_id.auto_create_payment_order = True
        if cls.invoice_manual.state == "draft":
            cls.invoice_manual.action_post()
        cls.aml_to_raise_warning = cls.invoice_manual.financial_move_line_ids[0]
        payment_order = cls.env["account.payment.order"].search(
            [
                ("state", "=", "draft"),
                ("payment_mode_id", "=", cls.invoice_manual.payment_mode_id.id),
            ]
        )
        cls._payment_order_all_workflow(cls, payment_order)
        # Altera o Modo de Pagamento apenas para testar esse caso sem Códigos
        cls.invoice_manual.payment_mode_id = cls.env.ref(
            "l10n_br_account_payment_order." "payment_mode_cheque"
        )

    def test_change_date_maturity_multiple(self):
        """Test Creation of a Payment Order an change MULTIPLE due date"""
        date_maturity = self.financial_move_line_ids.mapped("date_maturity")
        new_date = date.today() + relativedelta(years=1)
        self._send_and_check_new_cnab_code(
            self.invoice_auto,
            self.financial_move_line_ids,
            "change_date_maturity",
            "l10n_br_account_payment_order.manual_test_mov_instruction_code_06",
        )

        self.assertEqual(
            self.financial_move_line_0.date_maturity, new_date, "Data não alterada"
        )
        self.assertNotEqual(date_maturity[0], new_date, "Data não alterada")

    def test_change_date_maturity_one(self):
        """Test Creation of a Payment Order an change ONE due date"""
        date_maturity = self.financial_move_line_0.mapped("date_maturity")
        new_date = date.today() + relativedelta(years=1)
        self._send_and_check_new_cnab_code(
            self.invoice_auto,
            self.financial_move_line_0,
            "change_date_maturity",
            "l10n_br_account_payment_order.manual_test_mov_instruction_code_06",
        )

        self.assertEqual(
            self.env["account.move.line"]
            .browse(self.financial_move_line_0.id)
            .date_maturity,
            new_date,
            "Data não alterada",
        )
        self.assertNotEqual(date_maturity[0], new_date, "Data não alterada")

        # Caso Data de Vencimento igual
        self._send_and_check_new_cnab_code(
            self.invoice_auto,
            self.financial_move_line_0,
            "change_date_maturity",
            "l10n_br_account_payment_order.manual_test_mov_instruction_code_06",
            warning_error=True,
        )

        # Caso Sem Código CNAB
        self._send_and_check_new_cnab_code(
            self.invoice_manual,
            self.aml_to_raise_warning,
            "change_date_maturity",
            warning_error=True,
        )

    # def test_change_payment_mode(self):
    #     invoice = self.invoice_auto
    #     self._invoice_payment_order_all_workflow(
    #         invoice
    #     )
    #     financial_move_line_ids = invoice.financial_move_line_ids[0]
    #     with Form(self._prepare_change_view(financial_move_line_ids),
    #               view=self.chance_view_id) as f:
    #         f.change_type = 'change_payment_mode'
    #         f.payment_mode_id = self.env.ref(
    #             'l10n_br_account_payment_order.main_payment_mode_boleto')
    #     change_wizard = f.save()
    #     self.assertRaises(
    #         change_wizard.doit(), 'Favor melhorar este teste'
    #     )

    def test_change_not_payment(self):
        """Test Creation of a Payment Order an change not_payment"""
        self._send_and_check_new_cnab_code(
            self.invoice_auto,
            self.financial_move_line_0,
            "not_payment",
            "l10n_br_account_payment_order.manual_test_mov_instruction_code_02",
        )

        self._send_and_check_new_cnab_code(
            self.invoice_manual,
            self.aml_to_raise_warning,
            "not_payment",
            warning_error=True,
        )

    def test_change_protest_tittle(self):
        """Test Creation of a Payment Order an change protest_tittle"""
        self._send_and_check_new_cnab_code(
            self.invoice_auto,
            self.financial_move_line_0,
            "protest_tittle",
            "l10n_br_account_payment_order.manual_test_mov_instruction_code_09",
        )

        self._send_and_check_new_cnab_code(
            self.invoice_manual,
            self.aml_to_raise_warning,
            "protest_tittle",
            warning_error=True,
        )

    def test_change_suspend_protest_keep_wallet(self):
        """Test Creation of a Payment Order an change suspend_protest_keep_wallet"""
        self._send_and_check_new_cnab_code(
            self.invoice_auto,
            self.financial_move_line_0,
            "suspend_protest_keep_wallet",
            "l10n_br_account_payment_order.manual_test_mov_instruction_code_11",
        )

        self._send_and_check_new_cnab_code(
            self.invoice_manual,
            self.aml_to_raise_warning,
            "suspend_protest_keep_wallet",
            warning_error=True,
        )

    def test_change_suspend_grant_rebate(self):
        """Test Creation of a Payment Order an change grant_rebate"""
        self._send_and_check_new_cnab_code(
            self.invoice_auto,
            self.financial_move_line_0,
            "grant_rebate",
            "l10n_br_account_payment_order.manual_test_mov_instruction_code_04",
        )

        self._send_and_check_new_cnab_code(
            self.invoice_manual,
            self.aml_to_raise_warning,
            "grant_rebate",
            warning_error=True,
        )

    def test_change_grant_discount(self):
        """Test Creation of a Payment Order an change grant_discount"""
        self._send_and_check_new_cnab_code(
            self.invoice_auto,
            self.financial_move_line_0,
            "grant_discount",
            "l10n_br_account_payment_order.manual_test_mov_instruction_code_07",
        )

        self._send_and_check_new_cnab_code(
            self.invoice_manual,
            self.aml_to_raise_warning,
            "grant_discount",
            warning_error=True,
        )

    def test_change_suspend_cancel_rebate(self):
        """Test Creation of a Payment Order an change cancel_rebate"""
        self._send_and_check_new_cnab_code(
            self.invoice_auto,
            self.financial_move_line_0,
            "cancel_rebate",
            "l10n_br_account_payment_order.manual_test_mov_instruction_code_05",
        )

        self._send_and_check_new_cnab_code(
            self.invoice_manual,
            self.aml_to_raise_warning,
            "cancel_rebate",
            warning_error=True,
        )

    def test_change_suspend_cancel_discount(self):
        """Test Creation of a Payment Order an change cancel_discount"""
        self._send_and_check_new_cnab_code(
            self.invoice_auto,
            self.financial_move_line_0,
            "cancel_discount",
            "l10n_br_account_payment_order.manual_test_mov_instruction_code_08",
        )

        self._send_and_check_new_cnab_code(
            self.invoice_manual,
            self.aml_to_raise_warning,
            "cancel_discount",
            warning_error=True,
        )
