# @ 2020 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# @ 2020 KMEE - www.kmee.com.br
#   Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import time

from odoo.exceptions import UserError
from odoo.tests import SavepointCase, tagged


@tagged("post_install", "-at_install")
class TestPaymentOrderInbound(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.register_payments_model = cls.env["account.register.payments"].with_context(
            active_model="account.invoice"
        )
        cls.payment_model = cls.env["account.payment"]

        # Get Invoice for test
        cls.invoice_cef = cls.env.ref(
            "l10n_br_account_payment_order." "demo_invoice_payment_order_cef_cnab240"
        )
        cls.invoice_unicred = cls.env.ref(
            "l10n_br_account_payment_order."
            "demo_invoice_payment_order_unicred_cnab400"
        )

        cls.demo_invoice_auto = cls.env.ref(
            "l10n_br_account_payment_order." "demo_invoice_automatic_test"
        )

        # Journal
        cls.journal_cash = cls.env["account.journal"].search(
            [("type", "=", "cash")], limit=1
        )
        cls.payment_method_manual_in = cls.env.ref(
            "account.account_payment_method_manual_in"
        )

    def test_create_payment_order(self):
        """ Test Create Payment Order """

        # I check that Initially customer invoice is in the "Draft" state
        self.assertEqual(self.invoice_cef.state, "draft")

        # I validate invoice by creating on
        self.invoice_cef.action_invoice_open()

        # I check that the invoice state is "Open"
        self.assertEqual(self.invoice_cef.state, "open")

        # I check that now there is a move attached to the invoice
        assert self.invoice_cef.move_id, "Move not created for open invoice"

        payment_order = self.env["account.payment.order"].search(
            [("payment_mode_id", "=", self.invoice_cef.payment_mode_id.id)]
        )

        assert payment_order, "Payment Order not created."

        # TODO: Caso CNAB pode cancelar o Move ?
        #  Aparetemente isso precisa ser validado
        # Change status of Move to draft just to test
        self.invoice_cef.move_id.button_cancel()

        for line in self.invoice_cef.move_id.line_ids.filtered(
            lambda l: l.account_id.id == self.invoice_cef.account_id.id
        ):
            self.assertEqual(
                line.journal_entry_ref,
                line.invoice_id.name,
                "Error with compute field journal_entry_ref",
            )

        # Return the status of Move to Posted
        self.invoice_cef.move_id.action_post()

        # Verificar os campos CNAB na account.move.line
        for line in self.invoice_cef.move_id.line_ids.filtered(
            lambda l: l.account_id.id == self.invoice_cef.account_id.id
        ):
            assert (
                line.own_number
            ), "own_number field is not filled in created Move Line."
            assert line.mov_instruction_code_id, (
                "mov_instruction_code_id field is not filled" " in created Move Line."
            )
            self.assertEqual(
                line.journal_entry_ref,
                line.invoice_id.name,
                "Error with compute field journal_entry_ref",
            )
            # testar com a parcela 700
            if line.debit == 700.0:
                test_balance_value = line.get_balance()

        self.assertEqual(test_balance_value, 700.0, "Error with method get_balance()")

        payment_order = self.env["account.payment.order"].search(
            [("payment_mode_id", "=", self.invoice_cef.payment_mode_id.id)]
        )

        # Verifica os campos CNAB na linhas de pagamentos
        for line in payment_order.payment_line_ids:
            assert line.own_number, "own_number field is not filled in Payment Line."
            assert (
                line.mov_instruction_code_id
            ), "mov_instruction_code_id field are not filled in Payment Line."

        # Ordem de Pagto CNAB não pode ser apagada
        with self.assertRaises(UserError):
            payment_order.unlink()

        # Open payment order
        payment_order.draft2open()

        # Criação da Bank Line
        self.assertEqual(len(payment_order.bank_line_ids), 2)

        # A geração do arquivo é feita pelo modulo que implementa a
        # biblioteca a ser usada
        # Generate and upload
        # payment_order.open2generated()
        # payment_order.generated2uploaded()

        self.assertEqual(payment_order.state, "open")

        # Verifica os campos CNAB na linhas de bancarias
        for line in payment_order.bank_line_ids:
            assert line.own_number, "own_number field is not filled in Payment Line."
            assert (
                line.mov_instruction_code_id
            ), "mov_instruction_code_id field are not filled in Payment Line."

        # Ordem de Pagto CNAB não pode ser Cancelada
        with self.assertRaises(UserError):
            payment_order.action_done_cancel()

        # Testar Cancelamento
        self.invoice_cef.action_invoice_cancel()

    def test_payment_outside_cnab_payment_order_draft(self):
        """
        Caso de Pagamento ser feito quando a Ordem de Pagamento em Draft deve
        apagar as linhas de pagamentos.
        """
        # I validate invoice by creating on
        self.invoice_unicred.action_invoice_open()

        payment_order = self.env["account.payment.order"].search(
            [("payment_mode_id", "=", self.invoice_unicred.payment_mode_id.id)]
        )
        self.assertEqual(len(payment_order.payment_line_ids), 2)

        ctx = {
            "active_model": "account.invoice",
            "active_ids": [self.invoice_unicred.id],
        }
        register_payments = self.register_payments_model.with_context(ctx).create(
            {
                "payment_date": time.strftime("%Y") + "-07-15",
                "journal_id": self.journal_cash.id,
                "payment_method_id": self.payment_method_manual_in.id,
            }
        )

        # Caso a Ordem de Pagamento ainda não esteja Confirmada
        register_payments.create_payments()
        payment = self.payment_model.search([], order="id desc", limit=1)

        self.assertAlmostEquals(payment.amount, 1000)
        self.assertEqual(payment.state, "posted")
        self.assertEqual(self.invoice_unicred.state, "paid")
        # Linhas Apagadas
        self.assertEqual(len(payment_order.payment_line_ids), 0)

    def test_payment_outside_cnab_payment_order_open(self):
        """
        Caso de Pagamento ser feito quando a Ordem de Pagamento em Open deve
        gerar erro por ter uma Instrução CNAB a ser enviada.
        """
        # I validate invoice by creating on
        self.invoice_unicred.action_invoice_open()

        payment_order = self.env["account.payment.order"].search(
            [("payment_mode_id", "=", self.invoice_unicred.payment_mode_id.id)]
        )
        # Open payment order
        payment_order.draft2open()
        self.assertEqual(payment_order.state, "open")

        ctx = {
            "active_model": "account.invoice",
            "active_ids": [self.invoice_unicred.id],
        }
        register_payments = self.register_payments_model.with_context(ctx).create(
            {
                "payment_date": time.strftime("%Y") + "-07-15",
                "journal_id": self.journal_cash.id,
                "payment_method_id": self.payment_method_manual_in.id,
            }
        )

        # Erro de ter uma Instrução CNAB Pendente, como não é possivel gerar a
        # Ordem de Pagto o teste de crição de Write Off e Alteração do Valor do
        # Titulo no caso de um pagamento parcial precisa ser feito no modulo
        # que implementa biblioteca a ser usada.
        with self.assertRaises(UserError):
            register_payments.create_payments()

    def test_cancel_invoice_payment_order_draft(self):
        """ Test Cancel Invoice when Payment Order Draft."""

        # I validate invoice by creating on
        self.invoice_unicred.action_invoice_open()
        payment_order = self.env["account.payment.order"].search(
            [("payment_mode_id", "=", self.invoice_unicred.payment_mode_id.id)]
        )
        self.assertEqual(len(payment_order.payment_line_ids), 2)

        # Testar Cancelamento
        self.invoice_unicred.action_invoice_cancel()

        self.assertEqual(len(payment_order.payment_line_ids), 0)
        # Nesse caso a account.move deverá ter sido apagada
        self.assertEqual(len(self.invoice_unicred.move_id), 0)

    def test_payment_by_assign_outstanding_credit(self):
        """
        Caso de Pagamento com CNAB usando o assign_outstanding_credit
        """
        self.partner_akretion = self.env.ref("l10n_br_base.res_partner_akretion")
        # I validate invoice by creating on
        self.invoice_cef.action_invoice_open()

        payment_order = self.env["account.payment.order"].search(
            [("payment_mode_id", "=", self.invoice_cef.payment_mode_id.id)]
        )
        # Open payment order
        payment_order.draft2open()
        # Generate and upload
        # payment_order.open2generated()
        # payment_order.generated2uploaded()
        # self.assertEqual(payment_order.state, 'done')

        payment = self.env["account.payment"].create(
            {
                "payment_type": "inbound",
                "payment_method_id": self.env.ref(
                    "account.account_payment_method_manual_in"
                ).id,
                "partner_type": "customer",
                "partner_id": self.partner_akretion.id,
                "amount": 100,
                "journal_id": self.journal_cash.id,
            }
        )
        payment.post()
        credit_aml = payment.move_line_ids.filtered("credit")

        # Erro de ter uma Instrução CNAB Pendente, como não é possivel gerar a
        # Ordem de Pagto o teste completo de pagamento via
        # assign_outstanding_credit precisa ser feito no modulo que
        # implementa biblioteca a ser usada.
        with self.assertRaises(UserError):
            self.invoice_cef.assign_outstanding_credit(credit_aml.id)

    def test_payment_inbound_payment_in_cash_full(self):
        """Pay a invoice in cash, with a payment already registred to in the bank.
        Then we must cancel the boleto at the bank, creating a movement of "BAIXA".
        :return:
        """
        # I check that Initially customer invoice is in the "Draft" state
        self.assertEqual(self.demo_invoice_auto.state, "draft")

        # I validate invoice by creating on
        self.demo_invoice_auto.action_invoice_open()

        # I check that the invoice state is "Open"
        self.assertEqual(self.demo_invoice_auto.state, "open")

        # I check that now there is a move attached to the invoice
        assert self.demo_invoice_auto.move_id, "Move not created for open invoice"
        inv_payment_mode_id = self.demo_invoice_auto.payment_mode_id
        payment_order = self.env["account.payment.order"].search(
            [("state", "=", "draft"), ("payment_mode_id", "=", inv_payment_mode_id.id)]
        )
        # I check creation of Payment Order
        assert payment_order, "Payment Order not created."
        payment_order.draft2open()
        payment_order.open2generated()
        payment_order.generated2uploaded()
        payment_order.action_done()

        open_amount = self.demo_invoice_auto.residual
        # I totally pay the Invoice
        self.demo_invoice_auto.pay_and_reconcile(
            self.env["account.journal"].search([("type", "=", "cash")], limit=1),
            open_amount,
        )

        # I verify that invoice is now in Paid state
        self.assertEqual(
            self.demo_invoice_auto.state, "paid", "Invoice is not in Paid state"
        )

        change_payment_order = self.env["account.payment.order"].search(
            [("state", "=", "draft"), ("payment_mode_id", "=", inv_payment_mode_id.id)]
        )

        change_payment_order.draft2open()
        change_payment_order.open2generated()
        change_payment_order.generated2uploaded()
        change_payment_order.action_done()

        assert (
            self.env.ref(
                "l10n_br_account_payment_order.manual_test_mov_instruction_code_02"
            ).id
            in change_payment_order.payment_line_ids.mapped(
                "mov_instruction_code_id"
            ).ids
        ), "Payment Order with wrong mov_instruction_code_id"

    def test_payment_inbound_payment_in_cash_twice(self):
        """Pay a invoice in cash, with a payment already registred to in the bank.
        Then we must cancel the boleto at the bank, creating a movement of "BAIXA".
        :return:
        """
        # I check that Initially customer invoice is in the "Draft" state
        self.assertEqual(self.demo_invoice_auto.state, "draft")

        # I validate invoice by creating on
        self.demo_invoice_auto.action_invoice_open()

        # I check that the invoice state is "Open"
        self.assertEqual(self.demo_invoice_auto.state, "open")

        # I check that now there is a move attached to the invoice
        assert self.demo_invoice_auto.move_id, "Move not created for open invoice"
        inv_payment_mode_id = self.demo_invoice_auto.payment_mode_id
        payment_order = self.env["account.payment.order"].search(
            [("state", "=", "draft"), ("payment_mode_id", "=", inv_payment_mode_id.id)]
        )
        # I check creation of Payment Order
        assert payment_order, "Payment Order not created."
        payment_order.draft2open()
        payment_order.open2generated()
        payment_order.generated2uploaded()
        payment_order.action_done()

        # I totally pay the Invoice
        self.demo_invoice_auto.pay_and_reconcile(
            self.env["account.journal"].search([("type", "=", "cash")], limit=1), 300
        )

        self.demo_invoice_auto.pay_and_reconcile(
            self.env["account.journal"].search([("type", "=", "cash")], limit=1), 700
        )

        # I verify that invoice is now in Paid state
        self.assertEqual(
            self.demo_invoice_auto.state, "paid", "Invoice is not in Paid state"
        )

        change_payment_order = self.env["account.payment.order"].search(
            [("state", "=", "draft"), ("payment_mode_id", "=", inv_payment_mode_id.id)]
        )

        change_payment_order.draft2open()
        change_payment_order.open2generated()
        change_payment_order.generated2uploaded()
        change_payment_order.action_done()

        assert (
            self.env.ref(
                "l10n_br_account_payment_order.manual_test_mov_instruction_code_02"
            ).id
            in change_payment_order.payment_line_ids.mapped(
                "mov_instruction_code_id"
            ).ids
        ), "Payment Order with wrong mov_instruction_code_id"

    def test_payment_inbound_cancel_invoice_alread_registred(self):
        """Cancel the invoice with a payment that is already registred at the bank.
        For that you have to create bank movement of "BAIXA" after we cancel
        the invoice.
        :return:
        """
        # I check that Initially customer invoice is in the "Draft" state
        self.assertEqual(self.demo_invoice_auto.state, "draft")

        # I validate invoice by creating on
        self.demo_invoice_auto.action_invoice_open()

        # I check that the invoice state is "Open"
        self.assertEqual(self.demo_invoice_auto.state, "open")

        # I check that now there is a move attached to the invoice
        assert self.demo_invoice_auto.move_id, "Move not created for open invoice"
        inv_payment_mode_id = self.demo_invoice_auto.payment_mode_id
        payment_order = self.env["account.payment.order"].search(
            [("state", "=", "draft"), ("payment_mode_id", "=", inv_payment_mode_id.id)]
        )
        # I check creation of Payment Order
        assert payment_order, "Payment Order not created."
        payment_order.draft2open()
        payment_order.open2generated()
        payment_order.generated2uploaded()
        payment_order.action_done()

        self.demo_invoice_auto.action_invoice_cancel()

        change_payment_order = self.env["account.payment.order"].search(
            [("state", "=", "draft"), ("payment_mode_id", "=", inv_payment_mode_id.id)]
        )

        assert change_payment_order, "Payment Order not created."

        change_payment_order.draft2open()
        change_payment_order.open2generated()
        change_payment_order.generated2uploaded()
        change_payment_order.action_done()

        assert (
            self.env.ref(
                "l10n_br_account_payment_order.manual_test_mov_instruction_code_02"
            ).id
            in change_payment_order.payment_line_ids.mapped(
                "mov_instruction_code_id"
            ).ids
        ), "Payment Order with wrong mov_instruction_code_id"
