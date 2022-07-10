# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# Copyright (C) 2022-Today - Akretion (<https://akretion.com/pt-BR>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import SavepointCase, tagged


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

        cls.invoice = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "company_id": cls.company.id,
                "partner_id": cls.env.ref("l10n_br_base.res_partner_cliente1_sp").id,
                "payment_mode_id": cls.payment_mode.id,
                "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
                "fiscal_operation_id": cls.env.ref("l10n_br_fiscal.fo_venda").id,
                "document_serie_id": cls.env.ref(
                    "l10n_br_fiscal.empresa_lc_document_55_serie_1"
                ).id,
                "journal_id": cls.invoice_journal.id,
                "invoice_payment_term_id": cls.payment_term.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.env.ref("product.product_product_3").id,
                            "quantity": 1,
                            "price_unit": 450.0,
                            "name": "Product - Invoice Line Test",
                            "fiscal_operation_id": cls.env.ref(
                                "l10n_br_fiscal.fo_venda"
                            ).id,
                            "fiscal_operation_line_id": cls.env.ref(
                                "l10n_br_fiscal.fo_venda_venda"
                            ).id,
                            "account_id": cls.invoice_line_account_id.id,
                            "company_id": cls.company.id,
                            "partner_id": cls.env.ref(
                                "l10n_br_base.res_partner_cliente1_sp"
                            ).id,
                        },
                    )
                ],
            }
        )
        for line in cls.invoice.invoice_line_ids:
            line.with_context(
                check_move_validity=False
            )._onchange_fiscal_operation_line_id()
            line.with_context(check_move_validity=False)._onchange_fiscal_tax_ids()
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
        cls.invoice_demo_data.action_post()

    def test_nfe_generate_tag_pag(self):
        """Test NFe generate TAG PAG."""
        # Dados criados no teste
        for detPag in self.invoice.nfe40_detPag:
            self.assertEqual(detPag.nfe40_indPag, "1", "Error in nfe40_indPag field.")
            self.assertEqual(detPag.nfe40_tPag, "18", "Error in nfe40_tPag field.")
            self.assertEqual(detPag.nfe40_vPag, 472.5, "Error in nfe40_vPag field.")

        # Dados criados no dados de demonstração
        for detPag in self.invoice_demo_data.nfe40_detPag:
            self.assertEqual(detPag.nfe40_indPag, "1", "Error in nfe40_indPag field.")
            self.assertEqual(detPag.nfe40_tPag, "15", "Error in nfe40_tPag field.")
            self.assertEqual(detPag.nfe40_vPag, 1000.0, "Error in nfe40_vPag field.")

    def test_nfe_generate_tag_cobr_and_dup(self):
        """Test NFe generate TAG COBR e DUP."""
        # Dados criados no teste
        self.assertEqual(self.invoice.nfe40_vOrig, 472.5)
        self.assertEqual(self.invoice.nfe40_vDesc, 0.0)
        self.assertEqual(self.invoice.nfe40_vLiq, 472.5)
        self.assertEqual(self.invoice.nfe40_dup[0].nfe40_nDup, "001")
        venc = self.invoice.financial_move_line_ids[0].date_maturity
        self.assertEqual(self.invoice.nfe40_dup[0].nfe40_dVenc, venc)
        self.assertEqual(self.invoice.nfe40_dup[0].nfe40_vDup, 472.5)

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
        with self.assertRaises(UserError):
            self.invoice_demo_data.action_post()
