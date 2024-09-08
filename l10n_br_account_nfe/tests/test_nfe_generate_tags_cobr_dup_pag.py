# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# Copyright (C) 2022-Today - Akretion (<https://akretion.com/pt-BR>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import Form, SavepointCase, tagged


@tagged("post_install", "-at_install")
class TestGeneratePaymentInfo(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")

        # set default user company
        companies = cls.env["res.company"].search([])
        cls.env.user.company_ids = [(6, 0, companies.ids)]
        cls.env.user.company_id = cls.company

        cls.payment_mode = cls.env["account.payment.mode"].create(
            {
                "name": "Money",
                "company_id": cls.company.id,
                "payment_method_id": cls.env.ref(
                    "account.account_payment_method_manual_in"
                ).id,
                "fiscal_payment_mode": "18",
                "bank_account_link": "variable",
            }
        )

        cls.invoice_account_id = cls.env["account.account"].create(
            {
                "company_id": cls.company.id,
                "user_type_id": cls.env.ref("account.data_account_type_receivable").id,
                "code": "RECTEST",
                "name": "Test receivable account",
                "reconcile": True,
            }
        )

        cls.invoice_journal = cls.env["account.journal"].create(
            {
                "company_id": cls.company.id,
                "name": "Invoice Journal - (test)",
                "code": "INVTEST",
                "type": "sale",
            }
        )

        cls.payment_term = cls.env["account.payment.term"].create(
            {
                "name": "30 Days",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "balance",
                            "days": 30,
                            "option": "day_after_invoice_date",
                        },
                    )
                ],
            }
        )

        cls.invoice_line_account_id = cls.env["account.account"].create(
            {
                "company_id": cls.company.id,
                "user_type_id": cls.env.ref("account.data_account_type_revenue").id,
                "code": "705070",
                "name": "Product revenue account (test)",
            }
        )

        cls.fiscal_operation_id = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.fiscal_operation_id.deductible_taxes = True

        move_form = Form(
            cls.env["account.move"]
            .with_company(cls.company)
            .with_context(default_move_type="out_invoice")
        )
        move_form.partner_id = cls.env.ref("l10n_br_base.res_partner_cliente1_sp")
        move_form.document_type_id = cls.env.ref("l10n_br_fiscal.document_55")
        move_form.fiscal_operation_id = cls.fiscal_operation_id
        invoice_vals = move_form._values_to_save(all_fields=True)
        invoice_vals.update(
            {
                "company_id": cls.company.id,
                "currency_id": cls.company.currency_id.id,
                "payment_mode_id": cls.payment_mode.id,
                "document_serie_id": cls.env.ref(
                    "l10n_br_fiscal.empresa_lc_document_55_serie_1"
                ).id,
                "journal_id": cls.invoice_journal.id,
                "invoice_payment_term_id": cls.payment_term.id,
                "invoice_origin": "Teste l10n_br_account_nfe",
                "invoice_user_id": cls.env.user.id,
            }
        )

        line_form = move_form.invoice_line_ids.new()
        line_form.product_id = cls.env.ref("product.product_product_7")
        line_form.fiscal_operation_id = cls.fiscal_operation_id
        invoice_line_vals = line_form._values_to_save(all_fields=True)
        invoice_line_vals.update(
            {
                "account_id": cls.invoice_line_account_id.id,
                "quantity": 1,
                "product_uom_id": cls.env.ref("uom.product_uom_unit").id,
                "price_unit": 450.0,
                "name": "Product - Invoice Line Test",
                "fiscal_operation_line_id": cls.env.ref(
                    "l10n_br_fiscal.fo_venda_revenda"
                ).id,
                "company_id": cls.company.id,
                "partner_id": cls.env.ref("l10n_br_base.res_partner_cliente1_sp").id,
            }
        )

        invoice_vals["invoice_line_ids"].append((0, 0, invoice_line_vals))
        del invoice_vals["line_ids"]
        cls.invoice = cls.env["account.move"].create(invoice_vals)
        cls.invoice.invoice_line_ids._onchange_fiscal_tax_ids()
        cls.invoice.invoice_line_ids._onchange_fiscal_operation_line_id()
        cls.invoice.action_post()

        # Dado de Demonstração
        cls.invoice_demo_data = cls.env.ref(
            "l10n_br_account_nfe.demo_nfe_dados_de_cobranca"
        )
        cls.env.user.company_id = cls.invoice_demo_data.company_id
        for line in cls.invoice_demo_data.invoice_line_ids:
            line.with_context(
                check_move_validity=False
            )._onchange_fiscal_operation_line_id()
            line.with_context(check_move_validity=False)._onchange_fiscal_tax_ids()

    def test_nfe_generate_tag_pag(self):
        """Test NFe generate TAG PAG."""
        # Dados criados no teste
        for detPag in self.invoice.nfe40_detPag:
            self.assertEqual(detPag.nfe40_indPag, "1", "Error in nfe40_indPag field.")
            self.assertEqual(detPag.nfe40_tPag, "18", "Error in nfe40_tPag field.")
            self.assertEqual(detPag.nfe40_vPag, 450.0, "Error in nfe40_vPag field.")

        # Dados criados no dados de demonstração
        for detPag in self.invoice_demo_data.nfe40_detPag:
            self.assertEqual(detPag.nfe40_indPag, "1", "Error in nfe40_indPag field.")
            self.assertEqual(detPag.nfe40_tPag, "15", "Error in nfe40_tPag field.")
            self.assertEqual(detPag.nfe40_vPag, 1000.0, "Error in nfe40_vPag field.")

    def test_nfe_generate_tag_cobr_and_dup(self):
        """Test NFe generate TAG COBR e DUP."""
        # Dados criados no teste
        self.assertEqual(self.invoice.nfe40_vOrig, 450.0)
        self.assertEqual(self.invoice.nfe40_vDesc, 0.0)
        self.assertEqual(self.invoice.nfe40_vLiq, 450.0)
        self.assertEqual(self.invoice.nfe40_dup[0].nfe40_nDup, "001")
        venc = self.invoice.financial_move_line_ids[0].date_maturity
        self.assertEqual(self.invoice.nfe40_dup[0].nfe40_dVenc, venc)
        self.assertEqual(self.invoice.nfe40_dup[0].nfe40_vDup, 450.0)

        # Dados criados no dados de demonstração
        self.assertEqual(self.invoice_demo_data.nfe40_vOrig, 1000)
        self.assertEqual(self.invoice_demo_data.nfe40_vDesc, 0.0)
        self.assertEqual(self.invoice_demo_data.nfe40_vLiq, 1000)
        self.assertEqual(self.invoice_demo_data.nfe40_dup[0].nfe40_nDup, "001")
        venc = self.invoice_demo_data.financial_move_line_ids[0].date_maturity
        self.assertEqual(self.invoice_demo_data.nfe40_dup[0].nfe40_dVenc, venc)
        self.assertEqual(self.invoice_demo_data.nfe40_dup[0].nfe40_vDup, 330.0)

    def test_payment_mode_without_fiscal_mode(self):
        """Test when Payment Mode don't has Fiscal Mode."""
        self.pay_mode = self.env["account.payment.mode"].create(
            {
                "name": "Sem Meio Fiscal",
                "company_id": self.env.ref("l10n_br_base.empresa_simples_nacional").id,
                "payment_method_id": self.env.ref(
                    "account.account_payment_method_manual_in"
                ).id,
                # "fiscal_payment_mode": "18",
                "bank_account_link": "variable",
            }
        )
        self.invoice_demo_data.payment_mode_id = self.pay_mode.id
        with self.assertRaises(UserError) as captured_exception:
            self.invoice_demo_data.action_post()
        self.assertEqual(
            captured_exception.exception.args[0],
            (
                "Payment Mode Sem Meio Fiscal should have a "
                "Fiscal Payment Mode filled to be used in the Fiscal Document!"
            ),
        )

    def test_invoice_without_payment_mode(self):
        """Test Invoice without Payment Mode."""
        invoice = self.env.ref("l10n_br_account_nfe.demo_nfe_sem_dados_de_cobranca")
        invoice.action_post()
        self.assertFalse(
            invoice.nfe40_dup,
            "Error field nfe40_dup should not filled when Fiscal Operation are "
            "Bonificação.",
        )
        for detPag in invoice.nfe40_detPag:
            self.assertEqual(
                detPag.nfe40_tPag,
                "90",
                "Error in nfe40_tPag field, should be 90 - Sem Pagamento.",
            )

    def test_valid_nfe_xml(self):
        """
        Test that NFe XML is valid. This in fact tests that NFe computed fields are
        properly computed.
        In fact this tests this bug with dummy documents(lines) compute triggers
        https://github.com/OCA/l10n-brazil/issues/2451
        is fixed.
        """
        invoice = self.invoice
        invoice.fiscal_document_id._document_export()
        self.assertEqual(invoice.fiscal_document_id.xml_error_message, False)
