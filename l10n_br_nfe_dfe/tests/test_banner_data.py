# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import timedelta
from unittest import mock

from xsdata.formats.dataclass.transports import DefaultTransport

from odoo import fields
from odoo.tests.common import TransactionCase

from .test_nfe_dfe import response_sucesso_multiplos


class TestDfeBannerData(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")

    def _banner_data(self):
        return (
            self.env["res.company"]
            .with_company(self.company)
            .dfe_get_banner_data("nfe")
        )

    def test_never_queried(self):
        """Warns when DF-e has never been queried."""
        self.company.nfe_dfe_last_query = False
        self.company.nfe_dfe_next_query = False
        self.company.nfe_last_nsu = False
        self.company.nfe_max_nsu = False

        data = self._banner_data()
        self.assertTrue(data["never_queried"])
        self.assertTrue(data["inactivity_warning"])
        self.assertIsNone(data["inactivity_days"])
        self.assertIsNone(data["last_query"])
        self.assertEqual(data["last_nsu"], "0")
        self.assertEqual(data["max_nsu"], "0")
        self.assertFalse(data["nsu_synced"])

    def test_recent_query_nsu_synced(self):
        """A recent query raises no warning and reports the NSU as synced."""
        now = fields.Datetime.now()
        self.company.nfe_dfe_last_query = now
        self.company.nfe_dfe_next_query = now + timedelta(hours=1)
        self.company.nfe_last_nsu = "200"
        self.company.nfe_max_nsu = "200"

        data = self._banner_data()
        self.assertFalse(data["never_queried"])
        self.assertFalse(data["inactivity_warning"])
        self.assertEqual(data["inactivity_days"], 0)
        self.assertTrue(data["nsu_synced"])
        # Datetimes travel in the server format, for the client to localize.
        self.assertEqual(data["last_query"], fields.Datetime.to_string(now))

    def test_old_query_and_homologation(self):
        """Warns on inactivity over the threshold and flags homologation."""
        self.company.nfe_dfe_last_query = fields.Datetime.now() - timedelta(days=45)
        self.company.nfe_dfe_next_query = False
        self.company.nfe_environment = "2"

        data = self._banner_data()
        self.assertTrue(data["inactivity_warning"])
        self.assertEqual(data["inactivity_days"], 45)
        self.assertTrue(data["is_homologation"])
        self.assertIsNone(data["next_query"])

    def test_action_ids(self):
        """The NSU and log tiles carry the act_window ids to open."""
        data = self._banner_data()
        self.assertEqual(
            data["nsu_action_id"], self.env.ref("l10n_br_fiscal_dfe.dfe_action").id
        )
        self.assertEqual(
            data["log_action_id"],
            self.env.ref("l10n_br_fiscal_dfe.dfe_distribution_log_action").id,
        )

    @mock.patch.object(DefaultTransport, "post")
    def test_pending_imports(self, mock_post):
        """Counts complete NF-e documents with no fiscal document yet."""
        mock_post.return_value = response_sucesso_multiplos.encode("utf-8")
        self.company.nfe_dfe_last_query = fields.Datetime.now()
        self.company.nfe_dfe_search_documents()

        complete_docs = self.env["l10n_br_fiscal_dfe.document"].search(
            [
                ("company_id", "=", self.company.id),
                ("dfe_ids.document_type_dfe", "=", "complete"),
            ]
        )
        self.assertTrue(complete_docs, "DFe search should create complete documents")

        data = self._banner_data()
        self.assertEqual(data["pending_import_count"], len(complete_docs))

    @mock.patch.object(DefaultTransport, "post")
    def test_pending_imports_per_company(self, mock_post):
        """Only fiscal documents of the current company count as imported."""
        mock_post.return_value = response_sucesso_multiplos.encode("utf-8")
        self.company.nfe_dfe_last_query = fields.Datetime.now()
        self.company.nfe_dfe_search_documents()
        access_key = "35200159594315000157550010000000012062777161"

        # The issuer of an intercompany NF-e holds the same access key.
        issuer_doc = self.env.ref("l10n_br_nfe.demo_nfe_national_sale_for_same_state")
        self.assertEqual(issuer_doc.document_key, access_key)
        self.assertNotEqual(issuer_doc.company_id, self.company)
        self.assertEqual(self._banner_data()["pending_import_count"], 1)

        imported_doc = self.env.ref("l10n_br_fiscal.demo_nfe_purchase_same_state")
        self.assertEqual(imported_doc.company_id, self.company)
        imported_doc.document_key = access_key
        self.assertFalse(imported_doc.imported_document)
        self.assertEqual(self._banner_data()["pending_import_count"], 1)
        imported_doc.imported_document = True
        self.assertEqual(self._banner_data()["pending_import_count"], 0)
