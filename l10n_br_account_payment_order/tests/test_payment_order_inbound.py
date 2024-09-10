# @ 2020 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# @ 2020 KMEE - www.kmee.com.br
#   Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.exceptions import UserError
from odoo.fields import Date
from odoo.tests import SavepointCase, tagged
from odoo.tests.common import Form


@tagged("post_install", "-at_install")
class TestPaymentOrderInbound(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.register_payments_model = cls.env["account.payment.register"].with_context(
            active_model="account.move"
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
        cls.main_company = cls.env.ref("base.main_company")
        cls.journal_cash = cls.env["account.journal"].search(
            [("type", "=", "cash"), ("company_id", "=", cls.main_company.id)], limit=1
        )
        cls.payment_method_manual_in = cls.env.ref(
            "account.account_payment_method_manual_in"
        )
        cls.partner_akretion = cls.env.ref("l10n_br_base.res_partner_akretion")

    def test_create_payment_order(self):
        """Test Create Payment Order"""

        # I check that Initially customer invoice is in the "Draft" state
        self.assertEqual(self.invoice_cef.state, "draft")

        # I validate invoice by creating on
        self.invoice_cef.action_post()

        # I check that the invoice state is "Posted"
        self.assertEqual(self.invoice_cef.state, "posted")

        # I check that now there is a move attached to the invoice
        # assert self.invoice_cef.move_id, "Move not created for open invoice"

        payment_order = self.env["account.payment.order"].search(
            [("payment_mode_id", "=", self.invoice_cef.payment_mode_id.id)]
        )

        assert payment_order, "Payment Order not created."

        # Change status of Move to draft just to test
        self.invoice_cef.button_cancel()

        # Return the status of Move to Posted
        self.invoice_cef.action_post()

        # Verificar os campos CNAB na account.move.line
        for line in self.invoice_cef.line_ids.filtered(lambda line: line.own_number):
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

        payment_order = self.env["account.payment.order"].search(
            [("payment_mode_id", "=", self.invoice_cef.payment_mode_id.id)]
        )

        # Verifica os campos CNAB na linhas de pagamentos
        for line in payment_order.payment_line_ids:
            assert line.own_number, "own_number field is not filled in Payment Line."
            assert (
                line.instruction_move_code_id
            ), "instruction_move_code_id field are not filled in Payment Line."

        # Ordem de Pagto CNAB não pode ser apagada
        with self.assertRaises(UserError):
            payment_order.unlink()

        # Open payment order
        payment_order.draft2open()

        # A geração do arquivo é feita pelo modulo que implementa a
        # biblioteca a ser usada
        # Generate and upload
        # payment_order.open2generated()
        # payment_order.generated2uploaded()

        self.assertEqual(payment_order.state, "open")

        # Verifica os campos CNAB na linhas de pagamentos
        for line in payment_order.payment_line_ids:
            assert line.own_number, "own_number field is not filled in Payment Line."
            assert (
                line.instruction_move_code_id
            ), "instruction_move_code_id field are not filled in Payment Line."

        # Ordem de Pagto CNAB não pode ser Cancelada
        with self.assertRaises(UserError):
            payment_order.action_done_cancel()

        # Testar Cancelamento
        self.invoice_cef.button_cancel()

    def test_payment_outside_cnab_payment_order_draft(self):
        """
        Caso de Pagamento ser feito quando a Ordem de Pagamento em Draft deve
        apagar as linhas de pagamentos.
        """
        # I validate invoice by creating on
        self.invoice_unicred.action_post()

        payment_order = self.env["account.payment.order"].search(
            [("payment_mode_id", "=", self.invoice_unicred.payment_mode_id.id)]
        )
        self.assertEqual(len(payment_order.payment_line_ids), 2)

        ctx = {
            "active_model": "account.move",
            "active_ids": [self.invoice_unicred.id],
        }
        register_payments = self.register_payments_model.with_context(**ctx).create(
            {
                "payment_date": Date.context_today(self.env.user),
                "journal_id": self.journal_cash.id,
                "payment_method_id": self.payment_method_manual_in.id,
            }
        )

        # Caso a Ordem de Pagamento ainda não esteja Confirmada
        payment_id = register_payments._create_payments()
        payment = self.payment_model.browse(payment_id.id)

        self.assertAlmostEqual(payment.amount, 1000)
        self.assertEqual(payment.state, "posted")
        self.assertEqual(self.invoice_unicred.payment_state, "paid")
        # Linhas Apagadas
        self.assertEqual(len(payment_order.payment_line_ids), 0)

    def test_payment_outside_cnab_payment_order_open(self):
        """
        Caso de Pagamento ser feito quando a Ordem de Pagamento em Open deve
        gerar erro por ter uma Instrução CNAB a ser enviada.
        """
        # I validate invoice by creating on
        self.invoice_unicred.action_post()

        payment_order = self.env["account.payment.order"].search(
            [("payment_mode_id", "=", self.invoice_unicred.payment_mode_id.id)]
        )

        # Open payment order
        payment_order.draft2open()
        self.assertEqual(payment_order.state, "open")

        ctx = {
            "active_model": "account.move",
            "active_ids": [self.invoice_unicred.id],
        }
        register_payments = self.register_payments_model.with_context(**ctx).create(
            {
                "payment_date": Date.context_today(self.env.user),
                "journal_id": self.journal_cash.id,
                "payment_method_id": self.payment_method_manual_in.id,
            }
        )

        # Erro de ter uma Instrução CNAB Pendente, como não é possivel gerar a
        # Ordem de Pagto o teste de crição de Write Off e Alteração do Valor do
        # Titulo no caso de um pagamento parcial precisa ser feito no modulo
        # que implementa biblioteca a ser usada.
        with self.assertRaises(UserError):
            register_payments._create_payments()

    def test_cancel_invoice_payment_order_draft(self):
        """Test Cancel Invoice when Payment Order Draft."""

        # I validate invoice by creating on
        self.invoice_unicred.action_post()

        payment_order = self.env["account.payment.order"].search(
            [("payment_mode_id", "=", self.invoice_unicred.payment_mode_id.id)]
        )
        self.assertEqual(len(payment_order.payment_line_ids), 2)

        # Testar Cancelamento
        self.invoice_unicred.button_cancel()

        self.assertEqual(len(payment_order.payment_line_ids), 0)
        # TODO Na v13 ao cancelar uma invoice as linhas de lançamentos
        #  contabeis são mantidas, é preciso confirmar se em nenhum caso
        #  as linhas são apagadas para assim poder eliminar do Roadmap
        #  essa questão é os campos que foram sobreescritos no modulo
        #  para funcionar antes
        # Nesse caso a account.move deverá ter sido apagada
        # self.assertEqual(len(self.invoice_unicred.line_ids), 0)

    def test_payment_by_assign_outstanding_credit(self):
        """
        Caso de Pagamento com CNAB usando o assign_outstanding_credit
        """
        self.partner_akretion = self.env.ref("l10n_br_base.res_partner_akretion")
        # I validate invoice by creating on
        self.invoice_cef.action_post()

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
        payment.action_post()
        # TODO v13 metodo não encontrado mudou de nome?
        # credit_aml = payment.move_line_ids.filtered("credit")

        # Erro de ter uma Instrução CNAB Pendente, como não é possivel gerar a
        # Ordem de Pagto o teste completo de pagamento via
        # assign_outstanding_credit precisa ser feito no modulo que
        # implementa biblioteca a ser usada.
        # with self.assertRaises(UserError):
        #    self.invoice_cef.assign_outstanding_credit(credit_aml.id)

    def test_payment_inbound_payment_in_cash_full(self):
        """Pay a invoice in cash, with a payment already registred to in the bank.
        Then we must cancel the boleto at the bank, creating a movement of "BAIXA".
        :return:
        """
        # I check that Initially customer invoice is in the "Draft" state
        self.assertEqual(self.demo_invoice_auto.state, "draft")

        # I validate invoice by creating on
        self.demo_invoice_auto.action_post()

        # I check that the invoice state is "Posted"
        self.assertEqual(self.demo_invoice_auto.state, "posted")

        # I check that now there is a move attached to the invoice
        # assert self.demo_invoice_auto.move_id, "Move not created for open invoice"
        inv_payment_mode_id = self.demo_invoice_auto.payment_mode_id
        payment_order = self.env["account.payment.order"].search(
            [("state", "=", "draft"), ("payment_mode_id", "=", inv_payment_mode_id.id)]
        )
        # I check creation of Payment Order
        assert payment_order, "Payment Order not created."
        payment_order.draft2open()
        payment_order.open2generated()
        payment_order.generated2uploaded()

        open_amount = self.demo_invoice_auto.amount_residual
        # I totally pay the Invoice
        payment_register = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=self.demo_invoice_auto.ids,
            )
        )
        payment_register.journal_id = self.journal_cash
        payment_register.payment_method_id = self.payment_method_manual_in

        # Perform the partial payment by setting the amount at 300 instead of 500
        payment_register.amount = open_amount

        payment = payment_register.save()._create_payments()
        self.assertEqual(len(payment), 1)

        # I verify that invoice is now in Paid state
        self.assertEqual(
            self.demo_invoice_auto.payment_state,
            "paid",
            "Invoice is not in Paid state",
        )

        change_payment_order = self.env["account.payment.order"].search(
            [("state", "=", "draft"), ("payment_mode_id", "=", inv_payment_mode_id.id)]
        )

        change_payment_order.draft2open()
        change_payment_order.open2generated()
        change_payment_order.generated2uploaded()

        assert (
            self.env.ref(
                "l10n_br_account_payment_order.manual_test_mov_instruction_code_02"
            ).id
            in change_payment_order.payment_line_ids.mapped(
                "instruction_move_code_id"
            ).ids
        ), "Payment Order with wrong instruction_move_code_id"

    def test_payment_inbound_payment_in_cash_twice(self):
        """Pay a invoice in cash, with a payment already registred to in the bank.
        Then we must cancel the boleto at the bank, creating a movement of "BAIXA".
        :return:
        """
        # I check that Initially customer invoice is in the "Draft" state
        self.assertEqual(self.demo_invoice_auto.state, "draft")

        # I validate invoice by creating on
        self.demo_invoice_auto.action_post()

        # I check that the invoice state is "Posted"
        self.assertEqual(self.demo_invoice_auto.state, "posted")

        # I check that now there is a move attached to the invoice
        # assert self.demo_invoice_auto.move_id, "Move not created for open invoice"
        inv_payment_mode_id = self.demo_invoice_auto.payment_mode_id
        payment_order = self.env["account.payment.order"].search(
            [("state", "=", "draft"), ("payment_mode_id", "=", inv_payment_mode_id.id)]
        )
        # I check creation of Payment Order
        assert payment_order, "Payment Order not created."
        payment_order.draft2open()
        payment_order.open2generated()
        payment_order.generated2uploaded()

        # I pay partial Invoice
        payment_register = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=self.demo_invoice_auto.ids,
            )
        )
        payment_register.journal_id = self.journal_cash
        payment_register.payment_method_id = self.payment_method_manual_in

        # Perform the partial payment by setting the amount at 300 instead of 1000
        payment_register.amount = 300

        payment = payment_register.save()._create_payments()
        self.assertEqual(len(payment), 1)

        # I verify that invoice is now is Partial Paid state
        self.assertEqual(
            self.demo_invoice_auto.payment_state,
            "partial",
            "Invoice is not in Partial state",
        )

        # I totally pay the Invoice
        payment_register = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=self.demo_invoice_auto.ids,
            )
        )
        payment_register.journal_id = self.journal_cash
        payment_register.payment_method_id = self.payment_method_manual_in

        # Perform the partial payment by setting the amount at 700 instead of 500
        payment_register.amount = 700

        payment = payment_register.save()._create_payments()
        self.assertEqual(len(payment), 1)

        # I verify that invoice is now in Paid state
        self.assertEqual(
            self.demo_invoice_auto.payment_state,
            "paid",
            "Invoice is not in Paid state",
        )

        change_payment_order = self.env["account.payment.order"].search(
            [("state", "=", "draft"), ("payment_mode_id", "=", inv_payment_mode_id.id)]
        )

        change_payment_order.draft2open()
        change_payment_order.open2generated()
        change_payment_order.generated2uploaded()

        assert (
            self.env.ref(
                "l10n_br_account_payment_order.manual_test_mov_instruction_code_02"
            ).id
            in change_payment_order.payment_line_ids.mapped(
                "instruction_move_code_id"
            ).ids
        ), "Payment Order with wrong instruction_move_code_id"

    def test_payment_inbound_cancel_invoice_alread_registred(self):
        """Cancel the invoice with a payment that is already registred at the bank.
        For that you have to create bank movement of "BAIXA" after we cancel
        the invoice.
        :return:
        """
        # I check that Initially customer invoice is in the "Draft" state
        self.assertEqual(self.demo_invoice_auto.state, "draft")

        # I validate invoice by creating on
        self.demo_invoice_auto.action_post()

        # I check that the invoice state is "Posted"
        self.assertEqual(self.demo_invoice_auto.state, "posted")

        # I check that now there is a move attached to the invoice
        # assert self.demo_invoice_auto.move_id, "Move not created for open invoice"
        inv_payment_mode_id = self.demo_invoice_auto.payment_mode_id
        payment_order = self.env["account.payment.order"].search(
            [("state", "=", "draft"), ("payment_mode_id", "=", inv_payment_mode_id.id)]
        )
        # I check creation of Payment Order
        assert payment_order, "Payment Order not created."
        payment_order.draft2open()
        payment_order.open2generated()
        payment_order.generated2uploaded()

        self.demo_invoice_auto.button_cancel()

        change_payment_order = self.env["account.payment.order"].search(
            [("state", "=", "draft"), ("payment_mode_id", "=", inv_payment_mode_id.id)]
        )

        assert change_payment_order, "Payment Order not created."

        change_payment_order.draft2open()
        change_payment_order.open2generated()
        change_payment_order.generated2uploaded()

        assert (
            self.env.ref(
                "l10n_br_account_payment_order.manual_test_mov_instruction_code_02"
            ).id
            in change_payment_order.payment_line_ids.mapped(
                "instruction_move_code_id"
            ).ids
        ), "Payment Order with wrong instruction_move_code_id"
