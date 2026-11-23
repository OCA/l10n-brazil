# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.l10n_br_nfse_dfe.tests.test_nfse_dfe import (
    PROVIDER_CNPJ,
    nfse_xml,
)


@tagged("post_install", "-at_install")
class TestNfseIssuedBill(TransactionCase):
    """The NFS-e that the company issued in another system: confirm, print and
    generate the invoice of the customer."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        companies = cls.env["res.company"].search([])
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                tracking_disable=True,
                allowed_company_ids=companies.ids,
            )
        )

    def _issued(self):
        """The file of the test has the company as taker: the company is made its
        provider, and a stranger its taker."""
        content = (
            nfse_xml()
            .replace(b"81583054000129", b"12345678000195")
            .replace(PROVIDER_CNPJ.encode(), b"81583054000129")
        )
        model = self.env["l10n_br_fiscal.document"].with_company(self.company)
        if not hasattr(model, "action_generate_invoice"):
            self.skipTest("l10n_br_account_edi is not installed")
        documents, errors, _warnings = model._edi_import_files([("nfse.xml", content)])
        self.assertFalse(errors)
        self.assertEqual(documents.issuer, "company")
        return documents

    def _confirmed(self):
        documents = self._issued()
        documents.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        line = documents.fiscal_line_ids
        line.product_id = self.env["product.product"].create(
            {"name": "Service", "type": "service"}
        )
        line.action_resolve_line()
        documents.action_document_confirm()
        self.assertEqual(documents.state_edoc, "autorizada")
        return documents

    def test_the_nfse_issued_by_the_company_is_confirmed_and_printed(self):
        documents = self._confirmed()
        with patch(
            "odoo.addons.mail.models.mail_template.MailTemplate.send_mail"
        ) as send:
            action = documents.view_pdf()
        self.assertFalse(send.called)
        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertTrue(documents.file_report_id.raw.startswith(b"%PDF"))

    def test_the_invoice_of_the_nfse_issued_by_the_company(self):
        """The invoice asks for the series of the document, which the company may
        not have registered for the NFS-e: the one of the test is registered."""
        documents = self._issued()
        documents.document_serie_id = self.env["l10n_br_fiscal.document.serie"].create(
            {
                "code": "1",
                "name": "1",
                "document_type_id": documents.document_type_id.id,
                "company_id": self.company.id,
            }
        )
        documents.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        line = documents.fiscal_line_ids
        line.product_id = self.env["product.product"].create(
            {"name": "Service", "type": "service"}
        )
        line.action_resolve_line()
        documents.action_document_confirm()
        action = documents.action_generate_invoice()
        bill = self.env["account.move"].browse(action["res_id"])
        self.assertEqual(bill.move_type, "out_invoice")
        self.assertTrue(bill.imported_document)
