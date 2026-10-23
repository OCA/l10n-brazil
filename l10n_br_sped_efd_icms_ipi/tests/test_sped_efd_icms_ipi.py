# Copyright 2023 - TODAY, Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from os import path

from odoo.tests import common

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

    def _pull_from_odoo(self, ind_ativ):
        sped_mixin = self.env["l10n_br_sped.mixin"]
        sped_mixin._flush_registers("efd_icms_ipi")
        file_path = path.join(self.demo_path, "demo_efd_icms_ipi.txt")
        declaration = sped_mixin._import_file(file_path, "efd_icms_ipi")
        declaration.button_flush_registers()
        declaration.write({"IND_ATIV": ind_ativ, "CLAS_ESTAB_IND": "00"})
        declaration.button_populate_sped_from_odoo()
        return declaration

    def _count(self, declaration, register):
        return self.env[f"l10n_br_sped.efd_icms_ipi.{register}"].search_count(
            [("declaration_id", "=", declaration.id)]
        )

    def test_pull_skips_industrial_only_registers_for_other_activity(self):
        """Guia Pratico da EFD ICMS/IPI: the 0002 and the block K only exist
        when `IND_ATIV` of the 0000 is 0 (industry or equivalent)."""
        declaration = self._pull_from_odoo("1")
        self.assertEqual(self._count(declaration, "0005"), 1)
        for register in ("0002", "k010", "k100"):
            self.assertEqual(
                self._count(declaration, register),
                0,
                f"{register} must not be pulled for IND_ATIV = 1",
            )

    def test_pull_creates_industrial_registers_for_industry(self):
        declaration = self._pull_from_odoo("0")
        self.assertEqual(self._count(declaration, "0002"), 1)
        self.assertEqual(self._count(declaration, "k010"), 1)
        self.assertEqual(self._count(declaration, "k100"), 1)
        self.assertEqual(
            self.env["l10n_br_sped.efd_icms_ipi.0002"]
            .search([("declaration_id", "=", declaration.id)])
            .CLAS_ESTAB_IND,
            "00",
        )
