# @ 2018 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.tests import tagged
from odoo.tests import SavepointCase
from odoo.exceptions import ValidationError, UserError


@tagged('post_install', '-at_install')
class TestPaymentOrder(SavepointCase):

    @classmethod
    def setUpClass(self):
        super().setUpClass()

        # Get Invoice for test
        self.invoice_cef = self.env.ref(
            'l10n_br_account_payment_order.'
            'demo_invoice_payment_order_cef_cnab240'
        )

    def test_create_payment_order(self):
        """ Test Create Payment Order """

        # I check that Initially customer invoice is in the "Draft" state
        self.assertEquals(self.invoice_cef.state, 'draft')

        # I validate invoice by creating on
        self.invoice_cef.action_invoice_open()

        # I check that the invoice state is "Open"
        self.assertEquals(self.invoice_cef.state, 'open')

        # I check that now there is a move attached to the invoice
        assert self.invoice_cef.move_id, \
            "Move not created for open invoice"

        payment_order = self.env['account.payment.order'].search([
            ('payment_mode_id', '=', self.invoice_cef.payment_mode_id.id)
        ])

        assert payment_order, "Payment Order not created."

        # TODO: Caso CNAB pode cancelar o Move ?
        #  Aparetemente isso precisa ser validado
        # Change status of Move to draft just to test
        self.invoice_cef.move_id.button_cancel()

        for line in self.invoice_cef.move_id.line_ids.filtered(
                lambda l: l.account_id.id == self.invoice_cef.account_id.id):
            self.assertEquals(
                line.journal_entry_ref, line.invoice_id.name,
                "Error with compute field journal_entry_ref")

        # Return the status of Move to Posted
        self.invoice_cef.move_id.action_post()

        # Verificar os campos CNAB na account.move.line
        for line in self.invoice_cef.move_id.line_ids.filtered(
                lambda l: l.account_id.id == self.invoice_cef.account_id.id):
            assert line.own_number,\
                'own_number field is not filled in created Move Line.'
            assert line.mov_instruction_code_id, \
                'mov_instruction_code_id field is not filled in created Move Line.'
            self.assertEquals(
                line.journal_entry_ref, line.invoice_id.name,
                'Error with compute field journal_entry_ref')
            # testar com a parcela 700
            if line.debit == 700.0:
                test_balance_value = line.get_balance()

        self.assertEquals(
            test_balance_value, 700.0,
            'Error with method get_balance()')

        payment_order = self.env['account.payment.order'].search([
            ('payment_mode_id', '=', self.invoice_cef.payment_mode_id.id)
        ])

        # Verifica os campos CNAB na linhas de pagamentos
        for l in payment_order.payment_line_ids:
            assert l.own_number, \
                'own_number field is not filled in Payment Line.'
            assert l.mov_instruction_code_id, \
                'mov_instruction_code_id field are not filled in Payment Line.'

        # Ordem de Pagto CNAB não pode ser apagada
        with self.assertRaises(UserError):
            payment_order.unlink()

        # Open payment order
        payment_order.draft2open()

        # Criação da Bank Line
        self.assertEquals(len(payment_order.bank_line_ids), 2)

        # A geração do arquivo é feita pelo modulo que implementa a
        # biblioteca a ser usada
        # Generate and upload
        # payment_order.open2generated()
        # payment_order.generated2uploaded()

        self.assertEquals(payment_order.state, 'open')

        # Verifica os campos CNAB na linhas de bancarias
        for l in payment_order.bank_line_ids:
            assert l.own_number, \
                'own_number field is not filled in Payment Line.'
            assert l.mov_instruction_code_id, \
                'mov_instruction_code_id field are not filled in Payment Line.'

        # Ordem de Pagto CNAB não pode ser Cancelada
        with self.assertRaises(UserError):
            payment_order.action_done_cancel()

        # Testar Cancelamento
        # with self.assertRaises(UserError):
        self.invoice_cef.action_invoice_cancel()

    def test_bra_number_constrains(self):
        """ Test bra_number constrains. """
        self.banco_bradesco = self.env[
            'res.bank'].search([('code_bc', '=', '033')])
        with self.assertRaises(ValidationError):
            self.env[
                'res.partner.bank'].create(dict(
                    bank_id=self.banco_bradesco.id,
                    partner_id=self.ref('l10n_br_base.res_partner_akretion'),
                    bra_number='12345'
                ))
