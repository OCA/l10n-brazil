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
