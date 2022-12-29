# Copyright 2022 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from os import path

from odoo.tests import common
from odoo.addons import l10n_br_sped_spec


class SpedTest(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.demo_path = path.join(l10n_br_sped_spec.__path__[0], "demo")

    def test_import_ecd(self):
        self.env["l10n_br_sped.mixin"].flush_registers("ecd")
        self.env["l10n_br_sped.mixin"].import_file(self.demo_path + "/demo_ecd.txt", "ecd")
        sped = self.env["l10n_br_sped.mixin"].generate_sped_text("ecd")
        # print(sped)

    def test_import_ecf(self):
        self.env["l10n_br_sped.mixin"].flush_registers("ecf")
        # TODO self.env["l10n_br_sped.mixin"].import_file(self.demo_path + "/demo_ecf.txt", "ecf")

    def test_import_efd_icms_ipi(self):
        self.env["l10n_br_sped.mixin"].flush_registers("efd_icms_ipi")
        self.env["l10n_br_sped.mixin"].import_file(self.demo_path + "/demo_efd_icms_ipi.txt", "efd_icms_ipi")
        sped = self.env["l10n_br_sped.mixin"].generate_sped_text("efd_icms_ipi")
        # print(sped)

    def test_import_efd_pis_cofins(self):
        self.env["l10n_br_sped.mixin"].flush_registers("efd_pis_cofins")
        self.env["l10n_br_sped.mixin"].import_file(self.demo_path + "/demo_efd_pis_cofins_multi.txt", "efd_pis_cofins")
        sped = self.env["l10n_br_sped.mixin"].generate_sped_text("efd_pis_cofins")
        # print(sped)





