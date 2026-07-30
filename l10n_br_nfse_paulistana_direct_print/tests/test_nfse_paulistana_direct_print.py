# Copyright (C) 2023 Antônio S. P. Neto <neto@engene.one> - Engenere LTDA
#     (https://engenere.one).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.l10n_br_nfse.tests.test_fiscal_document_nfse_common import (
    TestFiscalDocumentNFSeCommon,
)


class TestNFSePaulistanaDirectPrint(TestFiscalDocumentNFSeCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company.provedor_nfse = "paulistana"
        cls.document = cls.nfse_same_state
        cls.document.write(
            {
                "document_number": "123456",
                "verify_code": "12345",
            }
        )

    def test_url_nfse_paulistana(self):
        """The print URL uses number, municipal registration and verify code."""
        inscricao = self.company.partner_id.l10n_br_im_code
        self.assertTrue(
            inscricao, "the test scenario requires the municipal registration"
        )
        self.assertEqual(
            self.document.url_nfse_paulistana,
            "https://nfe.prefeitura.sp.gov.br/contribuinte/notaprint.aspx"
            f"?nf=123456&inscricao={inscricao}&verificacao=12345",
        )

    def test_url_nfse_paulistana_incomplete(self):
        """Without one of the three values the URL is empty, not a broken link."""
        self.document.verify_code = False
        self.assertEqual(self.document.url_nfse_paulistana, "")

    def test_action_open_nfse_paulistana(self):
        """The action opens the computed URL in a new tab."""
        self.assertDictEqual(
            self.document.action_open_nfse_paulistana(),
            {
                "type": "ir.actions.act_url",
                "url": self.document.url_nfse_paulistana,
                "target": "new",
            },
        )

    def test_is_nfse_paulistana(self):
        """The technical flag requires an NFS-e and the Paulistana provider."""
        self.assertTrue(self.document.is_nfse_paulistana)

        self.document.document_type_id = self.env.ref("l10n_br_fiscal.document_55")
        self.assertFalse(self.document.is_nfse_paulistana)

        self.document.document_type_id = self.env.ref("l10n_br_fiscal.document_SE")
        self.company.provedor_nfse = False
        self.assertFalse(self.document.is_nfse_paulistana)
