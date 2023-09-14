# Copyright 2023 - TODAY, Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from os import path

from odoo.tests import common

from odoo.addons import l10n_br_sped_ecf


class SpedTest(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.demo_path = path.join(l10n_br_sped_ecf.__path__[0], "demo")

    # FIXME: the demo file is broken
    # def test_import_ecf(self):
    #     self.env["l10n_br_sped.mixin"]._flush_registers("ecf")
    #     file_path = path.join(self.demo_path, "demo_ecf.txt")
    #     self.env["l10n_br_sped.mixin"]._import_file(file_path, "ecf")
    #     sped = self.env["l10n_br_sped.mixin"]._generate_sped_text("ecf")
    #     with open(file_path) as f:
    #         target_content = f.read()
    #         self.assertEqual(sped.strip(), target_content.strip())
    #     print(sped)
