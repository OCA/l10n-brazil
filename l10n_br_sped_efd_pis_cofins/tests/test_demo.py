# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

import base64

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSpedEfdPisCofinsDemo(TransactionCase):
    """The demo goes the whole way: the file of the month is generated."""

    def test_the_demo_declaration_has_its_file(self):
        declaration = self.env.ref(
            "l10n_br_sped_efd_pis_cofins.demo_declaration", raise_if_not_found=False
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
        registers = {line.split("|")[1] for line in lines if line.count("|")}
        self.assertIn("0100", registers, "the accountant of the demo")
        self.assertIn("M200", registers, "the PIS of the assessment")
        self.assertIn("M600", registers, "the COFINS of the assessment")
        entry = [line for line in lines if line.startswith("|C170|")]
        self.assertTrue(entry, "the resale purchase of the demo")
        # cumulative regime: the entry has no credit
        self.assertIn("|70|", entry[0])

    def test_the_demo_opening_balance_of_credit(self):
        opening = self.env.ref(
            "l10n_br_sped_efd_pis_cofins.demo_credit_opening_pis",
            raise_if_not_found=False,
        )
        if not opening:
            self.skipTest("database without demo data")
        self.assertAlmostEqual(opening.sudo().balance, 262.50, places=2)
