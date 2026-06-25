# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# Copyright (C) 2022-Today - Akretion (<https://akretion.com/pt-BR>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import Form, tagged

from odoo.addons.l10n_br_account.tests.common import AccountMoveBRCommon

from .tools import load_account_nfe_fixture_files


@tagged("post_install", "-at_install")
class TestGeneratePaymentInfo(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        if not cls.env.ref(
            "l10n_br_base.empresa_lucro_presumido", raise_if_not_found=False
        ):
            load_account_nfe_fixture_files(cls.env)

        cls.env.user.groups_id |= cls.env.ref("l10n_br_nfe.group_manager")
        cls.env.user.groups_id |= cls.env.ref("l10n_br_fiscal.group_manager")
        cls.configure_normal_company_taxes()

        cls.payment_mode = cls.env["account.payment.mode"].create(
            {
                "name": "Money",
                "company_id": cls.company_data["company"].id,
                "payment_method_id": cls.env.ref(
                    "account.account_payment_method_manual_in"
                ).id,
                "fiscal_payment_mode": "18",
                "bank_account_link": "variable",
            }
        )

        cls.payment_term = cls.env["account.payment.term"].create(
            {
                "name": "30 Days",
                "line_ids": [
                    Command.create(
                        {
                            "value": "percent",
                            "value_amount": 100,
                            "delay_type": "days_after",
                            "nb_days": 30,
                        }
                    )
                ],
            }
        )

        partner = cls.env.ref("l10n_br_base.res_partner_cliente1_sp")
        move_form = Form(
            cls.env["account.move"].with_context(
                default_move_type="out_invoice",
                account_predictive_bills_disable_prediction=True,
            )
        )
        move_form.partner_id = partner
        move_form.currency_id = cls.company_data["currency"]
        move_form.document_type_id = cls.env.ref("l10n_br_fiscal.document_55")
        move_form.document_serie_id = cls.empresa_lc_document_55_serie_1
        # l10n_latam_invoice_document compatibility
        if "l10n_latam.document.type" in cls.env:
            latam_doc_type = cls.env["l10n_latam.document.type"].search(
                [("code", "=", "55"), ("country_id", "=", cls.env.ref("base.br").id)],
                limit=1,
            )
            if latam_doc_type and move_form.l10n_latam_use_documents:
                move_form.l10n_latam_document_type_id = latam_doc_type
        move_form.fiscal_operation_id = cls.env.ref("l10n_br_fiscal.fo_venda")
        move_form.invoice_date = "2019-01-01"
        move_form.payment_mode_id = cls.payment_mode
        move_form.invoice_payment_term_id = cls.payment_term
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = cls.product_a
            line_form.fiscal_operation_line_id = cls.env.ref(
                "l10n_br_fiscal.fo_venda_venda"
            )
        cls.invoice = move_form.save()
        cls.invoice.action_post()

        cls.invoice_demo_data = cls._create_second_invoice()

    @classmethod
    def _create_second_invoice(cls):
        payment_term = cls.env["account.payment.term"].create(
            {
                "name": "30/60/90 Days",
                "line_ids": [
                    Command.create(
                        {
                            "value": "percent",
                            "value_amount": 33.33,
                            "delay_type": "days_after",
                            "nb_days": 30,
                        }
                    ),
                    Command.create(
                        {
                            "value": "percent",
                            "value_amount": 33.33,
                            "delay_type": "days_after",
                            "nb_days": 60,
                        }
                    ),
                    Command.create(
                        {
                            "value": "percent",
                            "value_amount": 33.34,
                            "delay_type": "days_after",
                            "nb_days": 90,
                        }
                    ),
                ],
            }
        )
        payment_mode = cls.env["account.payment.mode"].create(
            {
                "name": "Boleto",
                "company_id": cls.company_data["company"].id,
                "payment_method_id": cls.env.ref(
                    "account.account_payment_method_manual_in"
                ).id,
                "fiscal_payment_mode": "15",
                "bank_account_link": "variable",
            }
        )
        partner = cls.env.ref("l10n_br_base.res_partner_akretion")
        move_form = Form(
            cls.env["account.move"].with_context(
                default_move_type="out_invoice",
                account_predictive_bills_disable_prediction=True,
            )
        )
        move_form.partner_id = partner
        move_form.currency_id = cls.company_data["currency"]
        move_form.document_type_id = cls.env.ref("l10n_br_fiscal.document_55")
        move_form.document_serie_id = cls.empresa_lc_document_55_serie_1
        # l10n_latam_invoice_document compatibility
        if "l10n_latam.document.type" in cls.env:
            latam_doc_type = cls.env["l10n_latam.document.type"].search(
                [("code", "=", "55"), ("country_id", "=", cls.env.ref("base.br").id)],
                limit=1,
            )
            if latam_doc_type and move_form.l10n_latam_use_documents:
                move_form.l10n_latam_document_type_id = latam_doc_type
        move_form.fiscal_operation_id = cls.env.ref("l10n_br_fiscal.fo_venda")
        move_form.invoice_date = "2019-01-01"
        move_form.payment_mode_id = payment_mode
        move_form.invoice_payment_term_id = payment_term
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = cls.env.ref("product.product_product_5")
            line_form.fiscal_operation_line_id = cls.env.ref(
                "l10n_br_fiscal.fo_venda_revenda"
            )
        invoice = move_form.save()
        invoice.action_post()
        return invoice

    def test_nfe_generate_tag_pag(self):
        """Test NFe generate TAG PAG."""
        # Dados criados no teste
        self.assertTrue(len(self.invoice.nfe40_detPag) > 0)
        for detPag in self.invoice.nfe40_detPag:
            self.assertEqual(detPag.nfe40_indPag, "1", "Error in nfe40_indPag field.")
            self.assertEqual(detPag.nfe40_tPag, "18", "Error in nfe40_tPag field.")
            self.assertEqual(detPag.nfe40_vPag, 1032.5, "Error in nfe40_vPag field.")

        # Dados criados no dados de demonstracao
        self.assertTrue(len(self.invoice_demo_data.nfe40_detPag) > 0)
        for detPag in self.invoice_demo_data.nfe40_detPag:
            self.assertEqual(detPag.nfe40_indPag, "1", "Error in nfe40_indPag field.")
            self.assertEqual(detPag.nfe40_tPag, "15", "Error in nfe40_tPag field.")
            self.assertEqual(detPag.nfe40_vPag, 147.0, "Error in nfe40_vPag field.")

    def test_nfe_generate_tag_cobr_and_dup(self):
        """Test NFe generate TAG COBR e DUP."""
        # Dados criados no teste - values include Brazilian fiscal taxes
        self.assertEqual(self.invoice.nfe40_vOrig, 1032.5)
        self.assertEqual(self.invoice.nfe40_vDesc, 0.0)
        self.assertEqual(self.invoice.nfe40_vLiq, 1032.5)
        self.assertEqual(self.invoice.nfe40_dup[0].nfe40_nDup, "001")
        venc = self.invoice.due_line_ids[0].date_maturity
        self.assertEqual(self.invoice.nfe40_dup[0].nfe40_dVenc, venc)
        self.assertEqual(self.invoice.nfe40_dup[0].nfe40_vDup, 1032.5)

        self.assertEqual(self.invoice_demo_data.nfe40_vOrig, 147.0)
        self.assertEqual(self.invoice_demo_data.nfe40_vDesc, 0.0)
        self.assertEqual(self.invoice_demo_data.nfe40_vLiq, 147.0)
        self.assertEqual(self.invoice_demo_data.nfe40_dup[0].nfe40_nDup, "001")
        venc = self.invoice_demo_data.due_line_ids[0].date_maturity
        self.assertEqual(self.invoice_demo_data.nfe40_dup[0].nfe40_dVenc, venc)
        self.assertTrue(self.invoice_demo_data.nfe40_dup[0].nfe40_vDup > 0)

    def test_payment_mode_without_fiscal_mode(self):
        partner = self.env.ref("l10n_br_base.res_partner_akretion")
        move_form = Form(
            self.env["account.move"].with_context(
                default_move_type="out_invoice",
                account_predictive_bills_disable_prediction=True,
            )
        )
        move_form.partner_id = partner
        move_form.document_type_id = self.env.ref("l10n_br_fiscal.document_55")
        move_form.document_serie_id = self.empresa_lc_document_55_serie_1
        # l10n_latam_invoice_document compatibility
        if "l10n_latam.document.type" in self.env:
            latam_doc_type = self.env["l10n_latam.document.type"].search(
                [("code", "=", "55"), ("country_id", "=", self.env.ref("base.br").id)],
                limit=1,
            )
            if latam_doc_type and move_form.l10n_latam_use_documents:
                move_form.l10n_latam_document_type_id = latam_doc_type
        move_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        move_form.invoice_date = "2019-01-01"
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.env.ref("product.product_product_5")
            line_form.fiscal_operation_line_id = self.env.ref(
                "l10n_br_fiscal.fo_venda_revenda"
            )
        draft_invoice = move_form.save()

        self.pay_mode = self.env["account.payment.mode"].create(
            {
                "name": "Sem Meio Fiscal",
                "company_id": self.company_data["company"].id,
                "payment_method_id": self.env.ref(
                    "account.account_payment_method_manual_in"
                ).id,
                "bank_account_link": "variable",
            }
        )
        draft_invoice.payment_mode_id = self.pay_mode.id

        # Constraint should not fail during draft flush; it must fail on post.
        self.env.flush_all()

        with self.assertRaises(UserError) as captured_exception:
            draft_invoice.action_post()
        self.assertEqual(
            captured_exception.exception.args[0],
            (
                "Payment Mode Sem Meio Fiscal should have a "
                "Fiscal Payment Mode filled to be used in the Fiscal Document!"
            ),
        )

    def test_invoice_without_payment_mode(self):
        move_form = Form(
            self.env["account.move"].with_context(
                default_move_type="out_invoice",
                account_predictive_bills_disable_prediction=True,
            )
        )
        move_form.partner_id = self.env.ref("l10n_br_base.res_partner_akretion")
        move_form.document_type_id = self.env.ref("l10n_br_fiscal.document_55")
        # l10n_latam_invoice_document compatibility
        if "l10n_latam.document.type" in self.env:
            latam_doc_type = self.env["l10n_latam.document.type"].search(
                [("code", "=", "55"), ("country_id", "=", self.env.ref("base.br").id)],
                limit=1,
            )
            if latam_doc_type and move_form.l10n_latam_use_documents:
                move_form.l10n_latam_document_type_id = latam_doc_type
        move_form.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_bonificacao")
        move_form.invoice_date = "2019-01-01"
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.env.ref("product.product_product_5")
            line_form.price_unit = 1000.0
            line_form.fiscal_operation_line_id = self.env.ref(
                "l10n_br_fiscal.fo_bonificacao_bonificacao"
            )
        invoice = move_form.save()
        invoice.action_post()
        self.assertFalse(invoice.nfe40_dup)
        for detPag in invoice.nfe40_detPag:
            self.assertEqual(detPag.nfe40_tPag, "90")

    def test_valid_nfe_xml(self):
        invoice = self.invoice
        invoice.fiscal_document_id._document_export()
        self.assertEqual(invoice.fiscal_document_id.xml_error_message, False)
