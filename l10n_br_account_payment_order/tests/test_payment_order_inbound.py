# Copyright (C) 2020-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# Copyright (C) 2020-Today - KMEE (<http://kmee.com.br>).
# @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from ..constants import get_boleto_especie_short_name
from .common import CNABTestCommon


@tagged("post_install", "-at_install")
class TestPaymentOrderInbound(CNABTestCommon):
    def test_invoice_button_add_to_pay_order(self):
        """Test Invoice Button to Add to a payment order"""
        self.pay_mode_cef.auto_create_payment_order = False
        self._invoice_confirm_workflow(self.invoice_cef_240)
        self.invoice_cef_240.create_account_payment_line()
        self._get_draft_payment_order(self.invoice_cef_240)

    def test_payment_order_import_wizard(self):
        """Test Payment Order Import Wizard"""
        self.pay_mode_cef.auto_create_payment_order = False
        self._invoice_confirm_workflow(self.invoice_cef_240)
        self.import_with_po_wizard(self.invoice_cef_240.payment_mode_id)

    def test_pay_order_inbound_cnab_workflow(self):
        """Test Payment Order Inbound CNAB workflow"""

        self._invoice_confirm_workflow(self.invoice_cef_240)
        payment_order = self._get_draft_payment_order(self.invoice_cef_240)
        self.assertEqual(len(payment_order.payment_line_ids), 2)
        # Change status of Move to draft just to test
        self.invoice_cef_240.button_cancel()
        self.assertEqual(len(payment_order.payment_line_ids), 0)
        # TODO Na v13 ao cancelar uma invoice as linhas de lançamentos
        #  contabeis são mantidas, é preciso confirmar se em nenhum caso
        #  as linhas são apagadas para assim poder eliminar do Roadmap
        #  essa questão é os campos que foram sobreescritos no modulo
        #  para funcionar antes
        # Nesse caso a account.move deverá ter sido apagada
        # self.assertEqual(len(self.invoice_cef_240.line_ids), 0)

        self._invoice_confirm_workflow(self.invoice_cef_240)

        # Verificar os campos CNAB na account.move.line
        for line in self.invoice_cef_240.line_ids.filtered(
            lambda line: line.own_number
        ):
            assert (
                line.own_number
            ), "own_number field is not filled in created Move Line."
            assert line.instruction_move_code_id, (
                "instruction_move_code_id field is not filled" " in created Move Line."
            )
            # testar com a parcela 700
            if line.debit == 700.0:
                test_balance_value = line.get_balance()

        self.assertEqual(test_balance_value, 700.0, "Error with method get_balance()")

        payment_order = self._get_draft_payment_order(self.invoice_cef_240)

        # Ordem de Pagto CNAB não pode ser apagada
        with self.assertRaises(UserError):
            payment_order.unlink()

        self._run_payment_order_workflow(payment_order)

        # Ordem de Pagto CNAB não pode ser Cancelada
        with self.assertRaises(UserError):
            payment_order.action_done_cancel()

        # Test Sending multiple CNAB Instruction Movements
        for change in self.changes_to_sending:
            self._send_new_cnab_instruction_code(
                self.invoice_cef_240,
                change.get("change_to_send"),
                change.get("code_to_check"),
            )

    def test_warning_when_cnab_config_dont_has_code(self):
        self._run_invoice_and_order_workflow(self.invoice_itau_400)
        aml_to_change = self.invoice_itau_400.due_line_ids[0]
        self.changes_to_sending.append(
            {
                "change_to_send": "change_date_maturity",
                "test_dates_are_equals": True,
            }
        )
        for change in self.changes_to_sending:
            test_dates_are_equals = False
            if change.get("test_dates_are_equals"):
                test_dates_are_equals = True
            # Caso not_payment não tem Warning
            if change.get("change_to_send") != "not_payment":
                self._send_new_cnab_code(
                    aml_to_change,
                    change.get("change_to_send"),
                    warning_error=True,
                    test_dates_are_equals=test_dates_are_equals,
                )

    def test_payment_outside_cnab_payment_order_draft(self):
        """
        Caso de Pagamento ser feito quando a Ordem de Pagamento em Draft deve
        apagar as linhas de pagamentos.
        """

        self._invoice_confirm_workflow(self.invoice_cef_240)
        payment_order = self._get_draft_payment_order(self.invoice_cef_240)
        self.assertEqual(len(payment_order.payment_line_ids), 2)

        # Caso a Ordem de Pagamento ainda não esteja Confirmada
        payment = self._make_payment(self.invoice_cef_240, 1000.0)

        self.assertAlmostEqual(payment.amount, 1000.0)
        self.assertEqual(payment.state, "posted")
        self.assertEqual(self.invoice_cef_240.payment_state, "in_payment")
        # Linhas Apagadas
        self.assertEqual(len(payment_order.payment_line_ids), 0)

    def test_payment_outside_cnab_payment_order_open(self):
        """
        Caso de Pagamento ser feito quando a Ordem de Pagamento em Open deve
        gerar erro por ter uma Instrução CNAB a ser enviada.
        """
        self._invoice_confirm_workflow(self.invoice_cef_240)
        payment_order = self._get_draft_payment_order(self.invoice_cef_240)
        payment_order.draft2open()
        self.assertEqual(payment_order.state, "open")

        # Erro de ter uma Instrução CNAB Pendente, como não é possivel gerar a
        # Ordem de Pagto o teste de crição de Write Off e Alteração do Valor do
        # Titulo no caso de um pagamento parcial precisa ser feito no modulo
        # que implementa biblioteca a ser usada.
        with self.assertRaises(UserError):
            self._make_payment(
                self.invoice_cef_240, self.invoice_cef_240.amount_residual
            )

    def test_payment_by_assign_outstanding_credit(self):
        """
        Caso de Pagamento com CNAB usando o assign_outstanding_credit
        """
        self._run_invoice_and_order_workflow(self.invoice_cef_240)
        self._make_payment(self.invoice_cef_240, 100)
        payment_order = self._get_draft_payment_order(self.invoice_cef_240)
        self.assertEqual(
            payment_order.cnab_config_id.change_title_value_code_id,
            payment_order.payment_line_ids.mapped("instruction_move_code_id"),
            "Payment Order with wrong instruction_move_code_id for Write Off",
        )

    def test_payment_inbound_payment_in_cash_full(self):
        """Pay a invoice in cash, with a payment already registred to in the bank.
        Then we must cancel the boleto at the bank, creating a movement of "BAIXA".
        :return:
        """
        self._run_invoice_and_order_workflow(self.invoice_cef_240)
        # I totally pay the Invoice
        payment = self._make_payment(
            self.invoice_cef_240, self.invoice_cef_240.amount_residual
        )
        self.assertEqual(len(payment), 1)

        # I verify that invoice is now in Paid state
        self.assertEqual(
            self.invoice_cef_240.payment_state,
            "in_payment",
            "Invoice is not in Paid state",
        )
        self._check_order_with_write_off_code(self.invoice_cef_240)

    def test_payment_inbound_payment_in_cash_twice(self):
        """Pay a invoice in cash, with a payment already registred to in the bank.
        Then we must cancel the boleto at the bank, creating a movement of "BAIXA".
        :return:
        """
        self._run_invoice_and_order_workflow(self.invoice_cef_240)
        payment = self._make_payment(self.invoice_cef_240, 300)
        self.assertEqual(len(payment), 1)

        self.assertEqual(
            self.invoice_cef_240.payment_state,
            "partial",
            "Invoice is not in Partial state",
        )

        # I totally pay the Invoice
        payment = self._make_payment(
            self.invoice_cef_240, self.invoice_cef_240.amount_residual
        )
        self.assertEqual(len(payment), 1)
        self.assertEqual(
            self.invoice_cef_240.payment_state,
            "in_payment",
            "Invoice is not in Paid state",
        )
        self._check_order_with_write_off_code(self.invoice_cef_240)

    def test_payment_inbound_cancel_invoice_already_registred(self):
        """Cancel the invoice with a payment that is already registred at the bank.
        For that you have to create bank movement of "BAIXA" after we cancel
        the invoice.
        :return:
        """
        self._run_invoice_and_order_workflow(self.invoice_cef_240)
        self.invoice_cef_240.button_cancel()
        self._check_order_with_write_off_code(self.invoice_cef_240)

    def test_cancel_invoice_no_payment_mode_pay(self):
        """Test Pay Invoice without payment mode in cash"""
        self._invoice_confirm_workflow(self.invoice_without_pay_mode)
        self.assertEqual(self.invoice_without_pay_mode.state, "posted")
        payment = self._make_payment(
            self.invoice_without_pay_mode,
            self.invoice_without_pay_mode.amount_residual,
        )
        self.assertEqual(len(payment), 1)
        self.assertEqual(
            self.invoice_without_pay_mode.payment_state,
            "paid",
            "Invoice is not in Paid state",
        )

    def test_cancel_invoice_no_payment_mode_cancel(self):
        """Test Cancel Invoice Without Payment Mode"""
        self._invoice_confirm_workflow(self.invoice_without_pay_mode)
        self.invoice_without_pay_mode.button_cancel()
        self.assertEqual(self.invoice_without_pay_mode.state, "cancel")

    def test_get_boleto_especies_short_name(self):
        # TODO: deveria estar sendo chamado por algum método?
        #  Verificar ao mudar o campo o boleto Especie de Char para Objeto
        name = get_boleto_especie_short_name("01")
        self.assertEqual(name, "DM")
        # Teste de Não encontrado
        not_found = get_boleto_especie_short_name("18")
        self.assertFalse(not_found)

    def test_constrains_payment_mode(self):
        """Test account.payment.mode Constrains methods"""
        with self.assertRaises(ValidationError):
            self.pay_mode_cef.write(
                {
                    "group_lines": True,
                }
            )

    def test_cnab_config(self):
        """Test CNAB Config validations"""
        with self.assertRaises(ValidationError):
            self.cnab_config_itau_400.cnab_sequence_id = self.cnab_seq_cef
        with self.assertRaises(ValidationError):
            self.cnab_config_itau_400.own_number_sequence_id = self.own_number_seq_cef
        with self.assertRaises(ValidationError):
            self.cnab_config_cef.boleto_discount_perc = 101
        with self.assertRaises(ValidationError):
            self.cnab_config_itau_400.boleto_wallet = False

    def test_payment_mode_without_payment_order(self):
        """Test Invoice when Payment Mode not generate Payment Order."""
        self._invoice_confirm_workflow(self.invoice_cheque)
        payment_order = self.env["account.payment.order"].search(
            [
                ("state", "=", "draft"),
                ("payment_mode_id", "=", self.invoice_cheque.payment_mode_id.id),
            ]
        )
        self.assertEqual(len(payment_order), 0)

    def test_bra_number_constrains(self):
        """Test bra_number constrains."""
        with self.assertRaises(UserError):
            self.env["res.partner.bank"].create(
                {
                    "bank_id": self.env.ref("l10n_br_base.res_bank_033").id,
                    "partner_id": self.partner_a.id,
                    "bra_number": "12345",
                }
            )
