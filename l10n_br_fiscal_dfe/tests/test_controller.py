# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import contextlib
from datetime import timedelta
from unittest import mock

from xsdata.formats.dataclass.transports import DefaultTransport

import odoo.http
from odoo import fields
from odoo.tests.common import TransactionCase

from ..controllers.main import DfeDocumentBannerController
from .test_dfe import response_sucesso_multiplos


@contextlib.contextmanager
def mock_request(env):
    """Push a mock request onto Odoo's request stack."""
    request = mock.Mock()
    request.env = env
    request.session.debug = ""
    odoo.http._request_stack.push(request)
    try:
        yield request
    finally:
        odoo.http._request_stack.pop()


class TestDfeController(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.controller = DfeDocumentBannerController()

    def _call_banner(self):
        env = self.env(context={"allowed_company_ids": [self.company.id]})
        with mock_request(env):
            return self.controller.document_banner()

    def test_banner_never_queried(self):
        """Banner warns when DF-e has never been queried."""
        self.company.dfe_last_query = False
        self.company.dfe_next_query = False
        self.company.last_nsu = False
        self.company.max_nsu = False

        result = self._call_banner()
        html = result["html"]
        self.assertIn("never been queried", html)

    def test_banner_recent_query_nsu_synced(self):
        """Banner with recent query shows no warning and NSU synced."""
        now = fields.Datetime.now()
        self.company.dfe_last_query = now
        self.company.dfe_next_query = now + timedelta(hours=1)
        self.company.last_nsu = "200"
        self.company.max_nsu = "200"

        result = self._call_banner()
        html = result["html"]
        self.assertNotIn("never been queried", html)
        self.assertNotIn("days ago", html)
        self.assertIn("Synced", html)

    def test_banner_old_query_and_homologation(self):
        """Banner warns on inactivity > 30 days and homologation environment."""
        self.company.dfe_last_query = fields.Datetime.now() - timedelta(days=45)
        self.company.dfe_next_query = False
        self.company.dfe_environment = "2"

        result = self._call_banner()
        html = result["html"]
        self.assertIn("45", html)
        self.assertIn("Homologa", html)

    @mock.patch.object(DefaultTransport, "post")
    def test_banner_with_pending_imports(self, mock_post):
        """Banner counts complete NF-e docs not yet imported."""
        mock_post.return_value = response_sucesso_multiplos.encode("utf-8")
        self.company.dfe_last_query = fields.Datetime.now()
        self.company.dfe_search_documents()

        complete_docs = self.env["l10n_br_fiscal_dfe.document"].search(
            [
                ("company_id", "=", self.company.id),
                ("dfe_ids.dfe_nfe_document_type", "=", "dfe_nfe_complete"),
            ]
        )
        self.assertTrue(complete_docs, "DFe search should create complete documents")

        result = self._call_banner()
        html = result["html"]
        # 1 procNFe not imported → pending count uses text-warning style
        self.assertIn("text-warning", html)
