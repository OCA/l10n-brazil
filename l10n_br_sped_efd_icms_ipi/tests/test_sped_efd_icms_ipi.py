# Copyright 2023 - TODAY, Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from datetime import date
from os import path

from odoo.tests import common
from odoo.tools.misc import format_date

from odoo.addons import l10n_br_sped_efd_icms_ipi
from odoo.addons.l10n_br_sped_base.models.sped_mixin import SPED_ENCODING


class SpedTest(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.demo_path = path.join(l10n_br_sped_efd_icms_ipi.__path__[0], "demo")

    def test_import_efd_icms_ipi(self):
        self.env["l10n_br_sped.mixin"]._flush_registers("efd_icms_ipi")
        file_path = path.join(self.demo_path, "demo_efd_icms_ipi.txt")
        sped_mixin = self.env["l10n_br_sped.mixin"]
        declaration = sped_mixin._import_file(file_path, "efd_icms_ipi")
        sped = declaration._generate_sped_text()
        with open(file_path, encoding=SPED_ENCODING) as f:
            target_content = f.read()
            # print(sped)
            self.assertEqual(sped.strip(), target_content.strip())

    def _create_inventory(self, dt_inv):
        self.env["l10n_br_sped.mixin"]._flush_registers("efd_icms_ipi")
        file_path = path.join(self.demo_path, "demo_efd_icms_ipi.txt")
        declaration = self.env["l10n_br_sped.mixin"]._import_file(
            file_path, "efd_icms_ipi"
        )
        return self.env["l10n_br_sped.efd_icms_ipi.h005"].create(
            {"declaration_id": declaration.id, "DT_INV": dt_inv, "MOT_INV": "01"}
        )

    def test_h005_name_is_the_inventory_date(self):
        h005 = self._create_inventory(date(2023, 1, 31))
        name = h005.name_get()[0][1]
        self.assertNotIn("l10n_br_sped.efd_icms_ipi.h005", name)
        self.assertIn(format_date(self.env, date(2023, 1, 31)), name)

    def test_h005_name_search_by_the_inventory_date(self):
        h005 = self._create_inventory(date(2023, 1, 31))
        other = h005.copy({"DT_INV": date(2022, 12, 31)})
        H005 = self.env["l10n_br_sped.efd_icms_ipi.h005"]
        domain = [("id", "in", (h005 | other).ids)]

        found = H005.name_search(format_date(self.env, date(2023, 1, 31)), args=domain)
        self.assertEqual([r[0] for r in found], h005.ids)

        self.assertFalse(H005.name_search("31/12/1999", args=domain))
