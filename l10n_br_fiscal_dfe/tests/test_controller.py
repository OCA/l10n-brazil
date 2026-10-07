# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from unittest import mock

import odoo.http
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_br_fiscal_dfe.controllers.main import DfeDocumentBannerController


class _FakeRequest:
    """Minimal request whose update_context really changes the env."""

    def __init__(self, env):
        self.env = env

    def update_context(self, **overrides):
        self.env = self.env(context=dict(self.env.context, **overrides))


class TestDfeBannerController(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.default_company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.active_company = cls.env.ref("l10n_br_base.empresa_simples_nacional")
        cls.controller = DfeDocumentBannerController()

    def test_banner_uses_active_company_from_context(self):
        """The banner follows the company sent by the web client context."""
        env = self.env(context={"allowed_company_ids": [self.default_company.id]})
        odoo.http._request_stack.push(_FakeRequest(env))
        try:
            with mock.patch(
                "odoo.addons.base.models.ir_qweb.IrQWeb._render",
                autospec=True,
                return_value="",
            ) as render:
                self.controller.document_banner(
                    fiscal_type="nfe",
                    context={"allowed_company_ids": [self.active_company.id]},
                )
        finally:
            odoo.http._request_stack.pop()
        values = render.call_args.args[2]
        self.assertEqual(values["company"], self.active_company)
