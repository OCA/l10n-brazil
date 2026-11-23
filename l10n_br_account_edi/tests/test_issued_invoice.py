# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import mock

from lxml import etree

from odoo import Command
from odoo.tests import tagged
from odoo.tools import format_date

from ..models.account_move import AccountMove
from .common import AccountEdiCase


@tagged("post_install", "-at_install")
class TestIssuedInvoice(AccountEdiCase):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.configure_normal_company_taxes()
        cls.move = cls.init_invoice(
            "out_invoice",
            products=[cls.product_a],
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            document_serie_id=cls.empresa_lc_document_55_serie_1,
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_venda"),
            fiscal_operation_lines=[cls.env.ref("l10n_br_fiscal.fo_venda_venda")],
        )
        cls.document = cls.move.fiscal_document_id
        cls.document_model = type(cls.env["l10n_br_fiscal.document"])

    def test_installments_of_the_invoice_come_from_the_due_lines(self):
        self.move.invoice_payment_term_id = self.payment_term

        installments = self.move._edi_installments()

        self.assertEqual([i.number for i in installments], ["001", "002"])
        self.assertEqual(
            [i.date_due for i in installments],
            self._due_lines(self.move).mapped("date_maturity"),
        )
        self.assertAlmostEqual(
            sum(i.amount for i in installments), self.move.amount_total, places=2
        )

    def test_payment_is_in_installments_when_a_due_date_is_after_the_invoice(self):
        # the module alone: the means of payment is not known (account_nfe gives it)
        patcher = mock.patch.object(
            type(self.move), "_edi_payment_means", return_value=""
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.move.invoice_payment_term_id = self.payment_term

        (payment,) = self.move._edi_payments()

        self.assertEqual(payment.term, "installments")
        self.assertEqual(payment.amount, self.move.amount_financial_total)
        self.assertEqual(payment.means, self.move._edi_payment_means())

    def test_means_of_payment_is_unknown_for_the_module_alone(self):
        self.assertEqual(AccountMove._edi_payment_means(self.move), "")

    def test_payment_is_in_cash_when_everything_is_due_on_the_invoice_date(self):
        self.move.invoice_payment_term_id = self.env.ref(
            "account.account_payment_term_immediate"
        )

        (payment,) = self.move._edi_payments()

        self.assertEqual(payment.term, "cash")

    def test_the_invoice_previews_the_installments(self):
        # the module alone: the means of payment is not known (account_nfe gives it)
        patcher = mock.patch.object(
            type(self.move), "_edi_payment_means", return_value=""
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.move.invoice_payment_term_id = self.payment_term

        summary = self.move.edi_payment_summary

        for installment in self.move._edi_installments():
            self.assertIn(format_date(self.env, installment.date_due), summary)
        self.assertIn("In installments", summary)
        self.assertIn("Net amount payable", summary)

    def test_the_preview_shows_the_gross_the_withholdings_and_the_net(self):
        self.move.invoice_payment_term_id = self.payment_term
        net = self.move.fiscal_amount_total
        field = self.move._fields["amount_tax_withholding"]
        self.env.cache.set(self.move, field, 10.0)
        self.move.invalidate_recordset(["edi_payment_summary"])

        summary = self.move.edi_payment_summary

        self.assertIn(f"{net + 10.0:,.2f}", summary)
        self.assertIn(f"{net:,.2f}", summary)
        self.assertIn("10.00", summary)

    def test_the_document_previews_the_installments_of_the_draft_invoice(self):
        self.move.invoice_payment_term_id = self.payment_term

        self.assertEqual(
            self.document._edi_display_installments(), self.move._edi_installments()
        )
        self.assertEqual(
            self.document._edi_display_payments(), self.move._edi_payments()
        )
        summary = self.document.edi_payment_summary
        for installment in self.move._edi_installments():
            self.assertIn(format_date(self.env, installment.date_due), summary)

    def test_nothing_is_written_in_the_document_until_the_invoice_is_posted(self):
        with (
            mock.patch.object(
                self.document_model, "_edi_set_installments", autospec=True
            ) as set_installments,
            mock.patch.object(
                self.document_model, "_edi_set_payments", autospec=True
            ) as set_payments,
        ):
            self.move.invoice_payment_term_id = self.payment_term
            self.assertTrue(self.move.edi_payment_summary)
            self.assertTrue(self.document.edi_payment_summary)
            self.env.flush_all()
            set_installments.assert_not_called()
            set_payments.assert_not_called()

            self.move.action_post()

        set_installments.assert_called_once_with(
            self.document, self.move._edi_installments()
        )
        set_payments.assert_called_once_with(self.document, self.move._edi_payments())

    def test_a_document_of_the_partner_is_not_written(self):
        document = self._imported_document()
        with mock.patch.object(
            self.document_model, "_edi_set_installments", autospec=True
        ) as set_installments:
            move = self.env["account.move"].import_fiscal_document(
                document, move_type="in_invoice"
            )
            self.env["account.move"].browse(move.id).action_post()

        set_installments.assert_not_called()

    def test_the_preview_is_only_for_a_draft_invoice(self):
        self.move.invoice_payment_term_id = self.payment_term
        self.move.action_post()

        self.assertFalse(self.move.edi_payment_summary)

    def test_screens_of_the_installments_with_a_fiscal_user(self):
        user = self.env["res.users"].create(
            {
                "name": "Fiscal and billing",
                "email": "fiscal-billing@example.com",
                "login": "edi_fiscal_billing",
                "company_id": self.company.id,
                "company_ids": [Command.set(self.company.ids)],
                "groups_id": [
                    Command.set(
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("l10n_br_fiscal.group_user").id,
                            self.env.ref("account.group_account_invoice").id,
                        ]
                    )
                ],
            }
        )
        self.move.invoice_payment_term_id = self.payment_term
        move = self.move.with_user(user)
        document = self.document.with_user(user)

        self.assertTrue(move.read(["edi_payment_summary"])[0]["edi_payment_summary"])
        self.assertTrue(
            document.read(["edi_payment_summary"])[0]["edi_payment_summary"]
        )
        move_arch = etree.fromstring(move.get_view(view_type="form")["arch"])
        self.assertTrue(move_arch.xpath("//field[@name='edi_payment_summary']"))
        document_arch = etree.fromstring(document.get_view(view_type="form")["arch"])
        self.assertTrue(
            document_arch.xpath("//button[@name='action_generate_invoice']")
        )
        self.assertTrue(document_arch.xpath("//field[@name='edi_payment_summary']"))

    def test_an_imported_document_of_the_company_is_invoiced_as_a_customer_one(self):
        document = self._own_imported_document()

        move = self.env["account.move"].browse(
            document.action_generate_invoice()["res_id"]
        )

        self.assertEqual(move.move_type, "out_invoice")
        self.assertEqual(move.fiscal_document_id, document)
        self.assertEqual(
            (document.document_number, document.document_serie), ("777", "001")
        )

    def test_posting_the_invoice_of_an_imported_document_of_the_company_writes_nothing(
        self,
    ):
        document = self._own_imported_document()
        model = type(document)
        with (
            mock.patch.object(
                model, "_edi_set_installments", autospec=True
            ) as set_installments,
            mock.patch.object(
                model, "_edi_set_payments", autospec=True
            ) as set_payments,
        ):
            move = self.env["account.move"].browse(
                document.action_generate_invoice()["res_id"]
            )
            self.assertFalse(move.edi_payment_summary)
            move.action_post()

        set_installments.assert_not_called()
        set_payments.assert_not_called()
        self.assertEqual(document.state_edoc, "autorizada")
