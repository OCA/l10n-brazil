# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo.tests.common import TransactionCase


class TestCustomerNFeRefund(TransactionCase):
    def setUp(self):
        super(TestCustomerNFeRefund, self).setUp()
        self.wizard_export = self.env["l10n_br_account_product.nfe_export_invoice"]
        self.wizard_refund = self.env["account.invoice.refund"]
        self.invoice_same_state = self.env.ref(
            "l10n_br_account_product.demo_nfe_same_state"
        )
        self.invoice_same_state._onchange_fiscal_document_id()
        self.invoice_same_state._onchange_fiscal()
        for line in self.invoice_same_state.invoice_line_ids:
            line._onchange_fiscal()
        self.invoice_same_state.with_context(
            {"fiscal_document_code": "55"}
        ).action_invoice_open()

    def test_customer_nfe_refund(self):
        """Test Customer NFe Refund."""
        self.wizard = self.wizard_export.create(
            {"file_type": "xml", "nfe_environment": "2"}
        )
        result_export = self.wizard.with_context(
            {
                "active_model": "account.invoice",
                "active_ids": self.invoice_same_state.id,
            }
        ).nfe_export()
        assert result_export, "Error in wizard to create XML file."

        self.invoice_same_state.action_sefaz_open()
        # I totally pay the Invoice
        self.invoice_same_state.pay_and_reconcile(
            self.env["account.journal"].search([("type", "=", "bank")], limit=1), 2000.0
        )

        # I verify that invoice is now in Paid state
        assert self.invoice_same_state.state == "paid", "Invoice is not in Paid state"
        self.wizard = self.wizard_refund.create(
            {"description": "Test refund sale invoice"}
        )
        result = self.wizard.with_context(
            {
                "active_model": "account.invoice",
                "active_ids": self.invoice_same_state.id,
            }
        ).invoice_refund()

        assert result, "Error in wizard to create Refund Invoice."

        domain_ids = [x for x in result["domain"] if x[0] == "id"][0]
        if domain_ids:
            invoice_refund_id = domain_ids[2][0]
            assert invoice_refund_id, "Invoice refund not created!"
            invoice_refund = self.env["account.invoice"].browse(invoice_refund_id)
            categ = self.invoice_same_state.fiscal_category_id
            assert (
                invoice_refund.fiscal_category_id.id
                == categ.refund_fiscal_category_id.id
            ), "Wrong refund fiscal category!"
            for line in invoice_refund.invoice_line_ids:
                assert line.cfop_id.code == "1201", "Wrong CFOP Code"
