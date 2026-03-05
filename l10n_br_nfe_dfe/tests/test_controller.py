# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import contextlib
from datetime import timedelta
from unittest import mock

import odoo.http
from odoo import fields
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_br_fiscal_dfe.controllers.main import DfeDocumentBannerController


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

    def _call_banner(self, fiscal_type="nfe"):
        env = self.env(context={"allowed_company_ids": [self.company.id]})
        with mock_request(env):
            return self.controller.document_banner(fiscal_type=fiscal_type)

    def test_banner_never_queried(self):
        """Banner warns when DF-e has never been queried."""
        self.company.nfe_dfe_last_query = False
        self.company.nfe_last_nsu = "0"
        self.company.nfe_max_nsu = "0"

        result = self._call_banner()
        html = result["html"]
        self.assertIn("Never been queried", html)

    def test_banner_recent_query_nsu_synced(self):
        """Banner with recent query shows no warning and NSU synced."""
        now = fields.Datetime.now()
        # Add the dynamic fields for testing
        self.company.nfe_dfe_last_query = now
        self.company.nfe_dfe_next_query = now + timedelta(hours=1)
        self.company.nfe_last_nsu = "200"
        self.company.nfe_max_nsu = "200"

        result = self._call_banner()
        html = result["html"]
        self.assertNotIn("Never been queried", html)
        self.assertIn("Synced", html)

    def test_banner_pending_imports(self):
        """Banner counts complete NF-e docs not yet imported."""
        doc = self.env["l10n_br_fiscal_dfe.document"].create(
            {
                "access_key": "35200159594315000157550010000000012062777161",
                "company_id": self.company.id,
                "fiscal_type": "nfe",
            }
        )
        self.env["l10n_br_fiscal_dfe.dfe"].create(
            {
                "access_key": doc.access_key,
                "company_id": self.company.id,
                "fiscal_type": "nfe",
                "document_type_dfe": "complete",
                "dfe_document_id": doc.id,
            }
        )

        result = self._call_banner()
        html = result["html"]
        # 1 procNFe not imported → pending count uses text-warning style
        self.assertIn("text-warning font-weight-bold", html)
