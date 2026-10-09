# Copyright 2026 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class NfseStructure(TransactionCase):
    def test_inherited_fields(self):
        # Checks if fields were properly mapped into concrete models
        self.assertIn("nfse10_CNPJ", self.env["res.company"]._fields.keys())
        self.assertIn("nfse10_opSimpNac", self.env["res.company"]._fields.keys())
        self.assertIn(
            "nfse10_cServ", self.env["l10n_br_fiscal.document.line"]._fields.keys()
        )

    def test_trib_issqn(self):
        """tribISSQN follows the ISSQN of the line.

        A taxable service keeps 1. ISSQN NT from the fiscal operation, such as
        the rental of movable goods, gives 4 (Não incidência); export and
        immunity come from the ISSQN eligibility chosen on the line.
        """
        Line = self.env["l10n_br_fiscal.document.line"]
        issqn_nt = self.env.ref("l10n_br_fiscal.tax_issqn_nt")
        issqn_5 = self.env.ref("l10n_br_fiscal.tax_issqn_5")
        cases = [
            ({"issqn_tax_id": issqn_5.id, "issqn_eligibility": "1"}, "1"),
            ({"issqn_tax_id": issqn_nt.id, "issqn_eligibility": "1"}, "4"),
            ({"issqn_tax_id": issqn_nt.id, "issqn_eligibility": "2"}, "4"),
            ({"issqn_tax_id": issqn_5.id, "issqn_eligibility": "2"}, "1"),
            ({"issqn_tax_id": issqn_5.id, "issqn_eligibility": "4"}, "3"),
            ({"issqn_tax_id": issqn_5.id, "issqn_eligibility": "5"}, "2"),
        ]
        for vals, expected in cases:
            with self.subTest(vals=vals):
                self.assertEqual(Line.new(vals).nfse10_tribISSQN, expected)
