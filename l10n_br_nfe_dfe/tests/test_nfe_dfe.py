# Copyright (C) 2023 - TODAY Felipe Zago - KMEE
# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import unittest
from unittest import mock

from xsdata.formats.dataclass.transports import DefaultTransport

from odoo.tests.common import TransactionCase

from odoo.addons.queue_job.tests.common import trap_jobs

from .mock_nfe_responses import response_656_with_nsu, response_sucesso_multiplos


class TestNFeDFe(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")

    def setUp(self):
        super().setUp()
        # FIX: Clear cache and reset state before every test to prevent bleeding
        self.company.invalidate_recordset()
        self.company.write(
            {
                "nfe_last_nsu": "0",
                "nfe_max_nsu": "0",
                "auto_manifest_nfe": False,
            }
        )
        # Clean up any generic records that might have survived
        self.env["l10n_br_fiscal_dfe.dfe"].search(
            [("company_id", "=", self.company.id)]
        ).unlink()
        self.env["l10n_br_fiscal_dfe.document"].search(
            [("company_id", "=", self.company.id)]
        ).unlink()

    def _search_nfe_dfe(self):
        return self.env["l10n_br_fiscal_dfe.dfe"].search(
            [("company_id", "=", self.company.id), ("fiscal_type", "=", "nfe")]
        )

    @mock.patch.object(DefaultTransport, "post")
    def test_nfe_search_documents_success(self, mock_post):
        mock_post.return_value = response_sucesso_multiplos

        self.company._nfe_dfe_document_distribution()

        self.assertEqual(self.company.nfe_last_nsu, "000000000000201")
        records = self._search_nfe_dfe()
        self.assertTrue(records)

        # Check parsing
        complete_dfe = records.filtered(lambda r: r.document_type_dfe == "complete")
        self.assertEqual(len(complete_dfe), 1)
        self.assertEqual(
            complete_dfe.dfe_document_id.emitter, "TESTE - Simples Nacional"
        )

    @mock.patch.object(DefaultTransport, "post")
    def test_nfe_cfop_extraction(self, mock_post):
        mock_post.return_value = response_sucesso_multiplos
        self.company._nfe_dfe_document_distribution()

        doc = self.env["l10n_br_fiscal_dfe.document"].search(
            [
                ("company_id", "=", self.company.id),
                ("access_key", "=", "35200159594315000157550010000000012062777161"),
            ]
        )
        # Force computation
        cfop_codes = doc.cfop_ids.mapped("code")
        self.assertIn("5102", cfop_codes)

    @mock.patch.object(DefaultTransport, "post")
    def test_nfe_auto_manifestation(self, mock_post):
        mock_post.return_value = response_sucesso_multiplos
        # Enable manifestation for this specific test
        self.company.write({"auto_manifest_nfe": True})

        with trap_jobs() as trap:
            self.company._nfe_dfe_document_distribution()
            # FIXME
            trap.assert_jobs_count(1)  # Should enqueue the MD-e confirmation job

        mde = self.env["l10n_br_nfe.md_event"].search(
            [("company_id", "=", self.company.id)]
        )
        # FIXME
        self.assertEqual(len(mde), 1)
        self.assertEqual(mde.event_type, "ciente")

    @unittest.skip("Requires valid NF-e XML with complete schema for xsdata parser")
    @mock.patch.object(DefaultTransport, "post")
    def test_nfe_import_document(self, mock_post):
        mock_post.return_value = response_sucesso_multiplos
        self.company._nfe_dfe_document_distribution()

        doc = self.env["l10n_br_fiscal_dfe.document"].search(
            [
                ("company_id", "=", self.company.id),
                ("access_key", "=", "35200159594315000157550010000000012062777161"),
            ]
        )

        fiscal_doc = doc.import_document()
        self.assertTrue(fiscal_doc, "Fiscal document should be created after import")
        self.assertEqual(
            fiscal_doc.document_key, "35200159594315000157550010000000012062777161"
        )

    @mock.patch.object(DefaultTransport, "post")
    def test_nfe_cooldown_656(self, mock_post):
        mock_post.return_value = response_656_with_nsu
        self.company.write({"nfe_last_nsu": "100"})

        self.company._nfe_dfe_document_distribution()

        self.assertEqual(
            self.company.nfe_last_nsu, "000000000000300", "Must recover NSU from 656"
        )
