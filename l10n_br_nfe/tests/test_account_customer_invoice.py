# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo.tests.common import TransactionCase


class TestCustomerInvoice(TransactionCase):
    def setUp(self):
        super(TestCustomerInvoice, self).setUp()
        # Não foi possível usar um arquivo de demo criado pelo YAML
        # todas as vezes que rodava os testes o valor total da invoice
        # era alterado gerando falha no teste de 'status' em 'paid'
        # da 'Invoice'
        self.invoice_customer_original = self.env.ref(
            "l10n_br_account_product.demo_invoice_original"
        )

    def test_customer_invoice_original(self):
        """Test if account.invoice still work as original desing."""
        # I check that Initially customer invoice is in the "Draft" state
        self.assertEquals(self.invoice_customer_original.state, "draft")

        self.invoice_customer_original._onchange_fiscal()

        for line in self.invoice_customer_original.invoice_line_ids:
            line._onchange_fiscal()

        # I change the state of invoice to "Proforma2" by clicking
        # PRO-FORMA button
        self.invoice_customer_original.action_invoice_proforma2()

        # I check that the invoice state is now "Proforma2"
        self.assertEquals(self.invoice_customer_original.state, "proforma2")

        # I check that there is no move attached to the invoice
        self.assertEquals(len(self.invoice_customer_original.move_id), 0)

        # I validate invoice by creating on
        self.invoice_customer_original.action_invoice_open()

        # I check that the invoice state is "Open"
        self.assertEquals(self.invoice_customer_original.state, "open")

        # I check that now there is a move attached to the invoice
        assert (
            self.invoice_customer_original.move_id
        ), "Move not created for open invoice"

        # I totally pay the Invoice
        self.invoice_customer_original.pay_and_reconcile(
            self.env["account.journal"].search([("type", "=", "bank")], limit=1), 1000.0
        )

        # I verify that invoice is now in Paid state
        assert (
            self.invoice_customer_original.state == "paid"
        ), "Invoice is not in Paid state"
