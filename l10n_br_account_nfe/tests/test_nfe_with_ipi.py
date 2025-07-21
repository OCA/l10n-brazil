from odoo.tests import tagged

from odoo.addons.l10n_br_account.tests.common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestNFeWithIPI(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref)
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.configure_normal_company_taxes()
        cls.env.user.groups_id |= cls.env.ref("l10n_br_nfe.group_manager")

        cls.payment_mode = cls.env["account.payment.mode"].create(
            {
                "name": "Cash",
                "company_id": cls.company_data["company"].id,
                "payment_method_id": cls.env.ref(
                    "account.account_payment_method_manual_in"
                ).id,
                "fiscal_payment_mode": "18",
                "bank_account_link": "variable",
            }
        )

        # Create the NFe with a product that has a default 5% IPI incidence.
        cls.move_out_venda = cls.init_invoice(
            move_type="out_invoice",
            products=[cls.product_b],
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            document_serie_id=cls.empresa_lc_document_55_serie_1,
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_venda"),
            fiscal_operation_lines=[cls.env.ref("l10n_br_fiscal.fo_venda_venda")],
            post=False,
        )
        cls.move_out_venda.payment_mode_id = cls.payment_mode
        cls.move_out_venda.action_post()

    def test_nfe_with_ipi(self):
        """
        Test IPI calculation in NFe.
        """
        # Check the IPI percentage and value on the product line
        product_line = self.move_out_venda.invoice_line_ids[0]
        self.assertEqual(product_line.ipi_percent, 5.00)
        self.assertEqual(product_line.ipi_value, 50.00)

        # Check the total values in the NFe
        self.assertEqual(self.move_out_venda.nfe40_vIPI, 50.0)
        self.assertEqual(self.move_out_venda.nfe40_vProd, 1000.00)
        self.assertEqual(self.move_out_venda.nfe40_vNF, 1050.00)

    def test_nfe_credit_note(self):
        """
        Test fiscal document field: nfe40_impostoDevol (no demo)
        """
        partner_a = self.env["res.partner"].create({"name": "Test partner A"})
        fiscal_doc = self.env["l10n_br_fiscal.document"].create(
            {
                "fiscal_operation_id": self.env.ref(
                    "l10n_br_fiscal.fo_devolucao_venda"
                ).id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "edoc_purpose": "4",
                "issuer": "company",
                "partner_id": partner_a.id,
                "fiscal_operation_type": "in",
            }
        )
        product_id = self.env.ref("product.product_product_10")
        fiscal_doc_line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": fiscal_doc.id,
                "name": "Return - credit note",
                "product_id": product_id.id,
                "fiscal_operation_type": "in",
                "fiscal_operation_id": self.env.ref(
                    "l10n_br_fiscal.fo_devolucao_venda"
                ).id,
                "fiscal_operation_line_id": self.env.ref(
                    "l10n_br_fiscal.fo_devolucao_venda_devolucao_venda"
                ).id,
                "p_devol": 50,
                "ipi_devol_value": 1,
            }
        )
        fiscal_doc_line._onchange_product_id_fiscal()

        self.assertEqual(fiscal_doc_line.nfe40_impostoDevol.nfe40_pDevol, 50.00)
        self.assertEqual(
            fiscal_doc_line.nfe40_impostoDevol.nfe40_IPI.nfe40_vIPIDevol, 1.00
        )
