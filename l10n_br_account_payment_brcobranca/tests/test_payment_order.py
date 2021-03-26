# @ 2021 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo.tests import tagged
from odoo.tests import SavepointCase
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestPaymentOrder(SavepointCase):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        # Get Invoice for test
        self.invoice_unicred = self.env.ref(
            'l10n_br_account_payment_order.'
            'demo_invoice_payment_order_unicred_cnab400'
        )

    def test_create_payment_order_with_brcobranca(self):
        """ Test Create Payment Order with BRCobranca."""

        # I validate invoice by creating on
        self.invoice_unicred.action_invoice_open()

        # I check that the invoice state is "Open"
        self.assertEquals(self.invoice_unicred.state, 'open')

        # Geração do Boleto
        self.invoice_unicred.view_boleto_pdf()

        payment_order = self.env['account.payment.order'].search([
            ('payment_mode_id', '=', self.invoice_unicred.payment_mode_id.id)
        ])

        bank_journal = self.env.ref(
            'l10n_br_account_payment_order.unicred_journal')

        payment_order.write({
            'journal_id': bank_journal.id
        })

        self.assertEquals(len(payment_order.payment_line_ids), 2)
        self.assertEquals(len(payment_order.bank_line_ids), 0)

        # Open payment order
        payment_order.draft2open()

        # Criação da Bank Line
        self.assertEquals(len(payment_order.bank_line_ids), 2)

        # Generate and upload
        payment_order.open2generated()
        payment_order.generated2uploaded()
        self.assertEquals(payment_order.state, 'done')

        # Ordem de Pagto CNAB não pode ser apagada
        with self.assertRaises(UserError):
             payment_order.unlink()

        bank_line = payment_order.bank_line_ids

        # Linhas Bancarias CNAB não podem ser apagadas
        with self.assertRaises(UserError):
            bank_line.unlink()

        # Ordem de Pagto CNAB não pode ser Cancelada
        with self.assertRaises(UserError):
            payment_order.action_done_cancel()
