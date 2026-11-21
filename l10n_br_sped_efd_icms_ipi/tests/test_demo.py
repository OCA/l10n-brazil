# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

import base64

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSpedEfdIcmsIpiDemo(TransactionCase):
    """The demo goes the whole way: the file of the month is generated."""

    def test_the_demo_declaration_has_its_file(self):
        declaration = self.env.ref(
            "l10n_br_sped_efd_icms_ipi.demo_declaration", raise_if_not_found=False
        )
        if not declaration:
            self.skipTest("database without demo data")
        declaration = declaration.sudo()
        attachment = (
            self.env["ir.attachment"]
            .sudo()
            .search(
                [
                    ("res_model", "=", declaration._name),
                    ("res_id", "=", declaration.id),
                ],
                order="id desc",
                limit=1,
            )
        )
        self.assertTrue(attachment, "the demo generates the file")
        lines = base64.b64decode(attachment.datas).decode("latin-1").splitlines()
        registers = {line.split("|")[1]: line for line in lines if line.count("|")}
        self.assertIn("0100", registers, "the accountant of the demo")
        entry = [line for line in lines if line.startswith("|C170|")]
        self.assertTrue(entry, "the resale purchase of the demo")
        self.assertIn("|1102|", entry[0])
        self.assertIn("|180,00|", entry[0])
        self.assertIn("E110", registers)
