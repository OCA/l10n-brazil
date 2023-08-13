# Copyright 2022 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from os import path

from odoo.tests import common
from odoo.addons import l10n_br_sped_ecd


class SpedTest(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.demo_path = path.join(l10n_br_sped_ecd.__path__[0], "demo")

    def test_import_ecd(self):
        self.env["l10n_br_sped.mixin"].flush_registers("ecd")
        file_path = path.join(self.demo_path, "demo_ecd.txt")
        self.env["l10n_br_sped.mixin"].import_file(file_path, "ecd")
        sped = self.env["l10n_br_sped.mixin"].generate_sped_text("ecd")
        with open(file_path) as f:
            target_content = f.read()
            self.assertEqual(sped.strip(), target_content.strip())
        # print(sped)
