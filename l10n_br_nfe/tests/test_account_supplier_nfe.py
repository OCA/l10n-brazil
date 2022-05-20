# @ 2019 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields
from odoo.tests.common import TransactionCase


class TestSupplierNFe(TransactionCase):
    def setUp(self):
        super(TestSupplierNFe, self).setUp()
        self.invoice_same_state = self.env.ref(
            "l10n_br_account_product.demo_nfe_supplier_same_state"
        )

    def test_supplier_nfe(self):
        """Test Supplier NFe."""
        self.invoice_same_state._onchange_fiscal_document_id()
        assert self.invoice_same_state.document_serie_id, (
            "Error with _onchange_fiscal_document_id() field "
            "document_serie_id is not mapped."
        )
        self.invoice_same_state._onchange_fiscal()
        assert self.invoice_same_state.fiscal_position_id, (
            "Error with _onchange_fiscal() method, field "
            "fiscal_position_id is not mapped."
        )
        self.assertEqual(
            self.invoice_same_state.state, "draft", "Invoice is not in Draft state."
        )

        for line in self.invoice_same_state.invoice_line_ids:
            line._onchange_fiscal()
            assert line.fiscal_position_id, (
                "Error with _onchange_fiscal() method in object"
                " account.invoice.line, field fiscal_position_id"
                " is not mapped."
            )
            assert line.cfop_id, (
                "Error with _onchange_fiscal() method in object"
                " account.invoice.line, field cfop_id"
                " is not mapped."
            )
            assert line.invoice_line_tax_ids, (
                "Error with _onchange_fiscal() method in object"
                " account.invoice.line, field invoice_line_tax_ids"
                " is not mapped."
            )

        self.invoice_same_state.with_context(
            {"fiscal_document_code": "55"}
        ).action_invoice_open()
        self.assertEqual(
            self.invoice_same_state.state, "open", "Invoice should be in state Open"
        )

        # Add a related document
        self.invoice_same_state.write(
            {
                "document_related_ids": (
                    0,
                    0,
                    {
                        "document_type_id": self.env.ref(
                            "l10n_br_fiscal.document_04"
                        ).id,
                        "document_serie": "4",
                        "state_id": self.env.ref("base.state_br_sp").id,
                        "document_date": fields.Datetime.now(),
                        "cpfcnpj_type": "cnpj",
                        "cnpj_cpf": "30.805.965/0001-12",
                        "inscr_est": "215031186110",
                    },
                )
            }
        )
