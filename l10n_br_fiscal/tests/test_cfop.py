# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestCfop(TransactionCase):
    def test_is_import_follows_the_code(self):
        """``is_import`` is a compute without depends, so it never refreshes."""
        cfop = self.env.ref("l10n_br_fiscal.cfop_1101")
        self.assertFalse(cfop.is_import)

        cfop.invalidate_recordset()
        cfop.code = "3101"
        self.assertTrue(cfop.is_import)
