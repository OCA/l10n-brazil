# Copyright 2026 KMEE (Ygor Carvalho <ygor.carvalho@kmee.com.br>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests.common import tagged

from .common import AccountMoveBRCommon


@tagged("post_install", "-at_install")
class TestDownloadFilesFromInvoice(AccountMoveBRCommon):
    """The buttons of the invoice list hand over the files of its fiscal document.

    The files live in l10n_br_fiscal_edi, which this module does not depend on,
    so the invoice only forwards the call and says something legible when there
    is no fiscal document behind it.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.invoice = cls.init_invoice(
            "out_invoice",
            products=cls.product_a,
            document_type=cls.env.ref("l10n_br_fiscal.document_55"),
            fiscal_operation=cls.env.ref("l10n_br_fiscal.fo_venda"),
            fiscal_operation_lines=[cls.env.ref("l10n_br_fiscal.fo_venda_venda")],
            document_serie_id=cls.env.ref("l10n_br_fiscal.document_55_serie_1"),
        )

    def test_the_invoice_gathers_its_own_fiscal_document(self):
        document = self.invoice.fiscal_document_id
        self.assertTrue(document)
        self.assertEqual(self.invoice._fiscal_documents_to_download(), document)

    def test_without_the_edi_module_the_answer_is_legible(self):
        """This module does not depend on l10n_br_fiscal_edi, so where the
        electronic document is absent the button says so instead of failing
        with a missing attribute."""
        with self.assertRaises(UserError):
            self.invoice._download_fiscal_files("action_that_does_not_exist")

    def test_an_invoice_without_a_fiscal_document_is_refused(self):
        plain = self.env["account.move"].create({"move_type": "entry", "line_ids": []})
        with self.assertRaises(UserError):
            plain._fiscal_documents_to_download()

    def test_a_selection_gathers_the_documents_of_every_invoice(self):
        other = self.invoice.copy()
        gathered = (self.invoice | other)._fiscal_documents_to_download()
        self.assertEqual(
            gathered,
            self.invoice.fiscal_document_id | other.fiscal_document_id,
        )
