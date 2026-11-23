# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import importlib.util
import os

from odoo.modules.module import get_module_path
from odoo.tests.common import TransactionCase


class TestAccountMigration(TransactionCase):
    """The update of l10n_br_account installs l10n_br_account_edi."""

    def _migrate(self):
        path = os.path.join(
            get_module_path("l10n_br_account"),
            "migrations",
            "16.0.18.3.1",
            "post-migration.py",
        )
        spec = importlib.util.spec_from_file_location("account_post_migration", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.migrate(self.env.cr, "16.0.18.3.0")

    def _state(self, name):
        return self.env["ir.module.module"].search([("name", "=", name)]).state

    def test_the_module_is_installed_when_the_import_is_in_use(self):
        module = self.env["ir.module.module"].search(
            [("name", "=", "l10n_br_account_edi")]
        )
        module.state = "uninstalled"
        self._migrate()
        self.assertEqual(self._state("l10n_br_account_edi"), "to install")
        # running it again changes nothing
        self._migrate()
        self.assertEqual(self._state("l10n_br_account_edi"), "to install")

    def test_nothing_is_installed_when_the_import_is_not_in_use(self):
        modules = self.env["ir.module.module"]
        modules.search([("name", "=", "l10n_br_account_edi")]).state = "uninstalled"
        modules.search([("name", "=", "l10n_br_fiscal_edi")]).state = "uninstalled"
        self._migrate()
        self.assertEqual(self._state("l10n_br_account_edi"), "uninstalled")
