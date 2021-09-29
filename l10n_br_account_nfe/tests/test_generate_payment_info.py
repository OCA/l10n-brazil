from odoo.tests.common import TransactionCase


class TestGeneratePaymentInfo(TransactionCase):
    def setUp(self):
        super(TestGeneratePaymentInfo, self).setUp()

        self.company = self.env.ref("l10n_br_base.empresa_lucro_presumido")

        self.payment_mode = self.env["account.payment.mode"].create(
            {
                "name": "Money",
                "company_id": self.company.id,
                "payment_method_id": self.env.ref(
                    "account.account_payment_method_manual_in"
                ).id,
                "fiscal_payment_mode": "18",
                "bank_account_link": "variable",
            }
        )

        self.invoice_account_id = self.env["account.account"].create(
            {
                "company_id": self.company.id,
                "user_type_id": self.env.ref("account.data_account_type_receivable").id,
                "code": "RECTEST",
                "name": "Test receivable account",
                "reconcile": True,
            }
        )

        self.invoice_journal = self.env["account.journal"].create(
            {
                "company_id": self.company.id,
                "name": "Invoice Journal - (test)",
                "code": "INVTEST",
                "type": "purchase",
                "update_posted": True,
            }
        )

        self.payment_term = self.env["account.payment.term"].create(
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

        self.invoice = self.env["account.invoice"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.env.ref("l10n_br_base.res_partner_cliente1_sp").id,
                "payment_mode_id": self.payment_mode.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_venda").id,
                "document_serie_id": self.env.ref(
                    "l10n_br_fiscal.empresa_lc_document_55_serie_1"
                ).id,
                "journal_id": self.invoice_journal.id,
                "payment_term_id": self.payment_term.id,
            }
        )

        self.invoice_line_account_id = self.env["account.account"].create(
            {
                "company_id": self.company.id,
                "user_type_id": self.env.ref("account.data_account_type_expenses").id,
                "code": "EXPTEST",
                "name": "Test expense account",
            }
        )

        self.line = self.env["account.invoice.line"].create(
            {
                "product_id": self.env.ref("product.product_product_3").id,
                "quantity": 1,
                "price_unit": 100,
                "invoice_id": self.invoice.id,
                "name": "something",
                "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_venda").id,
                "fiscal_operation_line_id": self.env.ref(
                    "l10n_br_fiscal.fo_venda_venda"
                ).id,
                "account_id": self.invoice_line_account_id.id,
            }
        )

        self.line._onchange_product_id_fiscal()
        self.line._onchange_commercial_quantity()
        self.line._onchange_ncm_id()
        self.line._onchange_fiscal_operation_id()
        self.line._onchange_fiscal_operation_line_id()
        self.line._onchange_fiscal_taxes()

        self.invoice.action_invoice_open()

    def test_generate_payment_info(self):

        for detPag in self.invoice.nfe40_detPag:
            self.assertEqual(detPag.nfe40_indPag, "1", "Error in nfe40_indPag field.")
            self.assertEqual(detPag.nfe40_tPag, "18", "Error in nfe40_tPag field.")
            self.assertEqual(detPag.nfe40_vPag, 472.5, "Error in nfe40_vPag field.")

    def test_generate_cobr_info(self):
        self.assertEqual(
            self.invoice.nfe40_cobr.nfe40_fat.nfe40_nFat, self.invoice.number
        )
        self.assertEqual(self.invoice.nfe40_cobr.nfe40_fat.nfe40_vOrig, 472.5)
        self.assertEqual(self.invoice.nfe40_cobr.nfe40_fat.nfe40_vDesc, 0.0)
        self.assertEqual(self.invoice.nfe40_cobr.nfe40_fat.nfe40_vLiq, 472.5)
        self.assertEqual(self.invoice.nfe40_cobr.nfe40_dup[0].nfe40_nDup, "001")
        venc = self.invoice.financial_move_line_ids[0].date_maturity
        self.assertEqual(self.invoice.nfe40_cobr.nfe40_dup[0].nfe40_dVenc, venc)
        self.assertEqual(self.invoice.nfe40_cobr.nfe40_dup[0].nfe40_vDup, 472.5)
