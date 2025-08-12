# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# Copyright (C) 2022-Today - Akretion (<https://akretion.com/pt-BR>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import Form, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestGeneratePaymentInfo(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")

        # set default user company
        companies = cls.env["res.company"].search([])
        cls.env.user.company_ids = [Command.set(companies.ids)]
        cls.env.user.company_id = cls.company
        # for some reason this invoice should be created with the popup mode.
        # it seems like a test framework glitch because in the browser it works fine
        cls.env.user.groups_id |= cls.env.ref(
            "l10n_br_account.group_line_fiscal_detail"
        )

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
                "account_type": "asset_receivable",
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
                        },
                    )
                ],
            }
        )

        cls.invoice_line_account_id = cls.env["account.account"].create(
            {
                "company_id": cls.company.id,
                "account_type": "income",
                "code": "705070",
                "name": "Product revenue account (test)",
            }
        )

        cls.fiscal_operation_id = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.fiscal_operation_id.deductible_taxes = True

        move_form = Form(
            cls.env["account.move"].with_context(default_move_type="out_invoice")
        )
        move_form.partner_id = cls.env.ref("l10n_br_base.res_partner_cliente1_sp")
        move_form.document_type_id = cls.env.ref("l10n_br_fiscal.document_55")
        move_form.fiscal_operation_id = cls.fiscal_operation_id
        move_form.document_type_id = cls.env.ref("l10n_br_fiscal.document_55")
        move_form.document_serie_id = cls.env.ref(
            "l10n_br_fiscal.empresa_lc_document_55_serie_1"
        )
        move_form.payment_mode_id = cls.payment_mode
        move_form.invoice_payment_term_id = cls.payment_term
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = cls.env.ref("product.product_product_7")
            line_form.price_unit = 450.0
        cls.invoice = move_form.save()
        cls.invoice._post()

        # Dado de Demonstração
        cls.invoice_demo_data = cls.env.ref(
            "l10n_br_account_nfe.demo_nfe_dados_de_cobranca"
        )
        cls.env.user.company_id = cls.invoice_demo_data.company_id

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
        venc = self.invoice.due_line_ids[0].date_maturity
        self.assertEqual(self.invoice.nfe40_dup[0].nfe40_dVenc, venc)
        self.assertEqual(self.invoice.nfe40_dup[0].nfe40_vDup, 450.0)

        # Dados criados no dados de demonstração
        self.assertEqual(self.invoice_demo_data.nfe40_vOrig, 1000)
        self.assertEqual(self.invoice_demo_data.nfe40_vDesc, 0.0)
        self.assertEqual(self.invoice_demo_data.nfe40_vLiq, 1000)
        self.assertEqual(self.invoice_demo_data.nfe40_dup[0].nfe40_nDup, "001")
        venc = self.invoice_demo_data.due_line_ids[0].date_maturity
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
            "Error field nfe40_dup should not filled when Fiscal Operation "
            "is Bonificaçã",
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
