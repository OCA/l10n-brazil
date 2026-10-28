# Copyright 2026 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import contextlib
from unittest import mock

import odoo.http
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


class TestNfseDfeBanner(TransactionCase):
    """The DF-e banner of the NFS-e list, rendered by the controller."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.controller = DfeDocumentBannerController()

    def _banner_html(self):
        env = self.env(context={"allowed_company_ids": [self.company.id]})
        with mock_request(env):
            return self.controller.document_banner(fiscal_type="nfse")["html"]

    def test_banner_buttons_call_the_nfse_methods(self):
        html = self._banner_html()
        self.assertIn("action_banner_search_all_nfse", html)
        self.assertIn("action_banner_specific_search_nfse", html)

    def test_banner_restricted_production_is_homologation(self):
        self.company.nfse_dfe_environment = "producao_restrita"
        self.assertIn("Homologa", self._banner_html())
        self.company.nfse_dfe_environment = "producao"
        self.assertNotIn("Homologa", self._banner_html())
