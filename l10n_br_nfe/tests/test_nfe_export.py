# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestNFeExport(TransactionCase):
    def setUp(self):
        super(TestNFeExport, self).setUp()
        self.wizard_export = self.env["l10n_br_account_product.nfe_export_invoice"]
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

    def test_export_xml(self):
        self.wizard = self.wizard_export.create(
            {"file_type": "xml", "nfe_environment": "2"}
        )
        result = self.wizard.with_context(
            {
                "active_model": "account.invoice",
                "active_ids": self.invoice_same_state.id,
            }
        ).nfe_export()
        assert result, "Error in wizard to create XML file."
