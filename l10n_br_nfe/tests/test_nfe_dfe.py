# Copyright (C) 2023 - TODAY Felipe Zago - KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# pylint: disable=line-too-long

from unittest import mock

from nfelib.nfe.ws.edoc_legacy import DocumentoElectronicoAdapter

from odoo.tests.common import TransactionCase

from odoo.addons.l10n_br_fiscal_dfe.tests.test_dfe import (
    mocked_post_error_status_code,
    mocked_post_success_multiple,
    mocked_post_success_single,
)

from ..models.mde import MDe


class TestNFeDFe(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.dfe_id = cls.env["l10n_br_fiscal.dfe"].create(
            {"company_id": cls.env.ref("l10n_br_base.empresa_lucro_presumido").id}
        )

    @mock.patch.object(
        DocumentoElectronicoAdapter,
        "_post",
        side_effect=mocked_post_success_single,
    )
    @mock.patch.object(MDe, "action_ciencia_emissao", return_value=None)
    def test_download_document_proc_nfe(self, _mock_post, _mock_ciencia):
        self.dfe_id.search_documents()

        self.dfe_id.import_documents()
        self.assertEqual(len(self.dfe_id.imported_document_ids), 1)
        self.assertEqual(
            self.dfe_id.imported_document_ids[0].document_key,
            "35200159594315000157550010000000012062777161",
        )

    @mock.patch.object(
        DocumentoElectronicoAdapter, "_post", side_effect=mocked_post_success_multiple
    )
    def test_search_dfe_success(self, _mock_post):
        self.dfe_id.search_documents()
        self.assertEqual(self.dfe_id.mde_ids[-1].nsu, self.dfe_id.last_nsu)

        mde1, mde2 = self.dfe_id.mde_ids
        self.assertEqual(mde1.company_id, self.dfe_id.company_id)
        self.assertEqual(mde1.key, "31201010588201000105550010038421171838422178")
        self.assertEqual(mde1.emitter, "ZAP GRAFICA E EDITORA EIRELI")
        self.assertEqual(mde1.cnpj_cpf, "10.588.201/0001-05")
        self.assertEqual(mde1.state, "pendente")

        attachment_1 = self.env["ir.attachment"].search([("res_id", "=", mde1.id)])
        self.assertTrue(attachment_1)

        self.assertEqual(mde2.company_id, self.dfe_id.company_id)
        self.assertEqual(mde2.key, "35200159594315000157550010000000012062777161")
        self.assertEqual(
            mde2.partner_id, self.env.ref("l10n_br_base.simples_nacional_partner")
        )
        self.assertEqual(mde2.cnpj_cpf, "59.594.315/0001-57")
        self.assertEqual(mde2.state, "pendente")

        attachment_2 = self.env["ir.attachment"].search([("res_id", "=", mde2.id)])
        self.assertTrue(attachment_2)

    @mock.patch.object(
        DocumentoElectronicoAdapter,
        "_post",
        side_effect=mocked_post_success_single,
    )
    @mock.patch.object(MDe, "action_ciencia_emissao", return_value=None)
    def test_import_documents(self, _mock_post, _mock_ciencia):
        self.dfe_id.search_documents()
        self.dfe_id.import_documents()

        document_id = self.dfe_id.mde_ids[0].document_id
        self.assertTrue(document_id)
        self.assertEqual(document_id.dfe_id, self.dfe_id)

        with mock.patch.object(
            DocumentoElectronicoAdapter,
            "_post",
            side_effect=mocked_post_error_status_code,
        ):
            xml = self.dfe_id._download_document("dummy")
            self.assertIsNone(xml)

    def test_create_mde(self):
        mde = self.dfe_id._create_mde_from_schema("dummy_v1.0", False)
        self.assertIsNone(mde)

        mde_id = self.env["l10n_br_nfe.mde"].create({"key": "123456789"})

        mock_resNFe = mock.MagicMock(spec=["chNFe"])
        mock_resNFe.chNFe = "123456789"
        resnfe_mde_id = self.dfe_id._create_mde_from_schema("resNFe_v1.0", mock_resNFe)
        self.assertEqual(resnfe_mde_id, mde_id)

        mock_procNFe = mock.MagicMock(spec=["protNFe"])
        mock_procNFe.protNFe.infProt.chNFe = "123456789"
        procnfe_mde_id = self.dfe_id._create_mde_from_schema(
            "procNFe_v1.0", mock_procNFe
        )
        self.assertEqual(procnfe_mde_id, mde_id)
