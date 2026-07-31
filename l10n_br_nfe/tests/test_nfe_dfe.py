# Copyright (C) 2023 - TODAY Felipe Zago - KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from unittest import mock

from requests.exceptions import RequestException

# The new mock target is the transport layer used by nfelib/brazil-fiscal-client
from xsdata.formats.dataclass.transports import DefaultTransport

from odoo.tests.common import TransactionCase

# We import the raw XML strings defined in the original test file.
# This allows us to reuse the test data without using the old,
# incompatible mock helper functions.
from odoo.addons.l10n_br_fiscal_dfe.tests.test_dfe import (
    response_sucesso_individual,
    response_sucesso_multiplos,
)

# This model import is part of the business logic being tested and remains.
from ..models.mde import MDe


class TestNFeDFe(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.dfe = cls.env["l10n_br_fiscal.dfe"].create({"company_id": cls.company.id})

    @mock.patch.object(DefaultTransport, "post")
    @mock.patch.object(MDe, "action_ciencia_emissao", return_value=None)
    def test_download_document_proc_nfe(self, mock_ciencia, mock_post):
        """Test downloading and importing a single NFe from a DFe search."""
        # The new mock simply returns the raw XML bytes from the imported fixture.
        mock_post.return_value = response_sucesso_individual.encode("utf-8")

        self.dfe.search_documents()  # This populates self.dfe.mde_ids
        self.dfe.import_documents()  # This creates the fiscal.document
        self.dfe.refresh()

        self.assertEqual(len(self.dfe.imported_document_ids), 1)
        # Note: The key in the single response is different from the original test,
        # we adjust the assertion to match the data in `response_sucesso_individual`.
        # You may need to update your fixture data if this key is incorrect.
        # Based on the XML provided in the previous prompt, this key should be correct.
        self.assertEqual(
            self.dfe.imported_document_ids[0].document_key,
            "35200159594315000157550010000000012062777161",
        )
        self.assertEqual(mock_post.call_count, 2)
        mock_ciencia.assert_called()  # Ensure ciencia was called

    @mock.patch.object(DefaultTransport, "post")
    def test_search_dfe_success(self, mock_post):
        """Test processing a DFe search with multiple documents."""
        mock_post.return_value = response_sucesso_multiplos.encode("utf-8")

        self.dfe.search_documents()
        self.assertEqual(self.dfe.mde_ids[-1].nsu, self.dfe.last_nsu)
        self.assertEqual(self.dfe.last_nsu, "000000000000201")
        self.assertEqual(len(self.dfe.mde_ids), 2)

        mde1, mde2 = self.dfe.mde_ids
        # Assertions for the first document (resNFe)
        self.assertEqual(mde1.company_id, self.dfe.company_id)
        # Note: The key in this fixture seems different, adjust as needed.
        # This key comes from the resNFe inside response_sucesso_multiplos.
        self.assertEqual(mde1.key, "31201010588201000105550010038421171838422178")
        self.assertEqual(mde1.emitter, "ZAP GRAFICA E EDITORA EIRELI")
        self.assertEqual(mde1.cnpj_cpf, "10.588.201/0001-05")
        self.assertEqual(mde1.state, "pendente")
        attachment_1 = self.env["ir.attachment"].search([("res_id", "=", mde1.id)])
        self.assertTrue(attachment_1)

        # Assertions for the second document (procNFe)
        self.assertEqual(mde2.company_id, self.dfe.company_id)
        # This key comes from the procNFe inside response_sucesso_multiplos.
        self.assertEqual(mde2.key, "35200159594315000157550010000000012062777161")
        self.assertEqual(mde2.cnpj_cpf, "59.594.315/0001-57")
        self.assertEqual(mde2.state, "pendente")
        attachment_2 = self.env["ir.attachment"].search([("res_id", "=", mde2.id)])
        self.assertTrue(attachment_2)

    @mock.patch.object(DefaultTransport, "post")
    @mock.patch.object(MDe, "action_ciencia_emissao", return_value=None)
    def test_import_documents(self, mock_ciencia, mock_post):
        """Test document import and failure of subsequent downloads."""
        # Part 1: Successful import
        mock_post.return_value = response_sucesso_individual.encode("utf-8")
        self.dfe.search_documents()
        self.dfe.import_documents()

        document_id = self.dfe.mde_ids[0].document_id
        self.assertTrue(document_id)
        self.assertEqual(document_id.dfe_id, self.dfe)

        # Part 2: Mock a failed download attempt
        # We simulate an HTTP error by raising RequestException.
        mock_post.side_effect = RequestException("Mocked HTTP Error")
        xml = self.dfe._download_document("dummy_key_to_trigger_download")
        self.assertIsNone(xml)

    def test_create_mde(self):
        """This test doesn't use web services and needs no changes."""
        mde = self.dfe._create_mde_from_schema("dummy_v1.0", False)
        self.assertIsNone(mde)

        mde_id = self.env["l10n_br_nfe.mde"].create({"key": "123456789"})

        mock_resNFe = mock.MagicMock()
        # The structure of the mock object needs to match what the code expects
        mock_resNFe.chNFe = "123456789"
        resnfe_mde_id = self.dfe._create_mde_from_schema("resNFe_v1.00", mock_resNFe)
        self.assertEqual(resnfe_mde_id, mde_id)

        mock_procNFe = mock.MagicMock()
        # Match the attribute access chain: .protNFe.infProt.chNFe
        mock_procNFe.protNFe.infProt.chNFe = "123456789"
        procnfe_mde_id = self.dfe._create_mde_from_schema("procNFe_v4.00", mock_procNFe)
        self.assertEqual(procnfe_mde_id, mde_id)
