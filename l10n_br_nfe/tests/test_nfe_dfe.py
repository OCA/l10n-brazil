# Copyright (C) 2023 - TODAY Felipe Zago - KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from unittest import mock

from nfelib.nfe.ws.edoc_legacy import DocumentoElectronicoAdapter

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_br_fiscal_dfe.tests.test_dfe import (
    mocked_post_success_multiple,
    mocked_post_success_single,
)


class TestNFeDFe(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.dfe_monitor = cls.env["l10n_br_fiscal.dfe_monitor"].create(
            {"company_id": cls.env.ref("l10n_br_base.empresa_lucro_presumido").id}
        )

    @mock.patch.object(
        DocumentoElectronicoAdapter, "_post", side_effect=mocked_post_success_single
    )
    def test_download_document_proc_nfe(self, _mock_post):
        self.dfe_monitor.search_documents()
        self.dfe_monitor.dfe_ids.import_document()

        self.assertEqual(len(self.dfe_monitor.dfe_ids.document_id), 1)
        self.assertEqual(
            self.dfe_monitor.dfe_ids.document_id[0].document_key,
            "35200159594315000157550010000000012062777161",
        )

    @mock.patch.object(
        DocumentoElectronicoAdapter, "_post", side_effect=mocked_post_success_multiple
    )
    def test_search_dfe_success(self, _mock_post):
        self.dfe_monitor.search_documents()
        self.assertEqual(self.dfe_monitor.dfe_ids[0].nsu, self.dfe_monitor.last_nsu)

        dfe2, dfe1 = self.dfe_monitor.dfe_ids
        self.assertEqual(dfe1.company_id, self.dfe_monitor.company_id)
        self.assertEqual(dfe1.key, "31201010588201000105550010038421171838422178")
        self.assertEqual(dfe1.emitter, "ZAP GRAFICA E EDITORA EIRELI")
        self.assertEqual(dfe1.vat, "10.588.201/0001-05")
        self.assertEqual(dfe1.dfe_nfe_document_type, "dfe_nfe_summary")
        self.assertEqual(dfe1.nsu, "000000000000200")
        self.assertEqual(
            dfe1.display_name,
            "31201010588201000105550010038421171838422178 - Resumo da NF-e",
        )
        self.assertEqual(dfe1.dfe_access_key_id.color_status, "blue")
        self.assertEqual(
            dfe1.dfe_access_key_id.display_name,
            "31201010588201000105550010038421171838422178",
        )

        self.assertEqual(
            dfe1.dfe_access_key_id.key, "31201010588201000105550010038421171838422178"
        )

        self.assertEqual(dfe2.company_id, self.dfe_monitor.company_id)
        self.assertEqual(dfe2.key, "35200159594315000157550010000000012062777161")
        self.assertEqual(
            dfe2.partner_id, self.env.ref("l10n_br_base.simples_nacional_partner")
        )
        self.assertEqual(dfe2.vat, "59.594.315/0001-57")
        self.assertEqual(dfe2.dfe_nfe_document_type, "dfe_nfe_complete")
        self.assertEqual(dfe2.emitter, "TESTE - Simples Nacional")
        self.assertEqual(dfe2.document_amount, 14.0)

        self.assertEqual(
            dfe2.dfe_access_key_id.key, "35200159594315000157550010000000012062777161"
        )
        self.assertEqual(
            dfe2.display_name,
            "35200159594315000157550010000000012062777161 - NF-e Completa",
        )
        self.assertEqual(dfe2.dfe_access_key_id.color_status, "green")
        self.assertEqual(
            dfe2.dfe_access_key_id.display_name,
            "35200159594315000157550010000000012062777161",
        )

    @mock.patch.object(
        DocumentoElectronicoAdapter, "_post", side_effect=mocked_post_success_single
    )
    def test_generate_danfe(self, _mock_post):
        self.dfe_monitor.search_documents()
        dfe = self.dfe_monitor.dfe_ids

        result = dfe.dfe_access_key_id.make_pdf()

        self.assertEqual(result["type"], "ir.actions.act_url")
        self.assertTrue(result["url"].startswith("/web/content/"))
        self.assertIn("download=true", result["url"])

    @mock.patch.object(
        DocumentoElectronicoAdapter, "_post", side_effect=mocked_post_success_multiple
    )
    def test_download_documents(self, _mock_post):
        self.dfe_monitor.search_documents()
        dfe2, dfe1 = self.dfe_monitor.dfe_ids

        attachment_2 = self.env["ir.attachment"].search([("res_id", "=", dfe2.id)])
        self.assertTrue(attachment_2)

        result_dfe2 = dfe1.action_download_xml()
        attachment_single_dfe2 = self.get_attachment_from_result(result_dfe2)
        self.assertTrue(attachment_single_dfe2)
        self.assertEqual(attachment_single_dfe2, dfe1.attachment_id)

        result_dfe_2_access_key = dfe2.dfe_access_key_id.action_download_xml()
        attachment_single_dfe2_access_key = self.get_attachment_from_result(
            result_dfe_2_access_key
        )

        self.assertTrue(attachment_single_dfe2_access_key)

        with self.assertRaises(UserError):
            dfe1.dfe_access_key_id.action_download_xml()

    def get_attachment_from_result(self, result):
        _, _, _, att_id, _ = result["url"].split("/")
        return self.env["ir.attachment"].browse(int(att_id))
