# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase


class TestDataAbstractSearch(TransactionCase):
    """Odoo 19 turns a ("many2one_field", "=", "<code>") search into an "in"
    search on the display name of the comodel, so the fiscal data models
    (l10n_br_fiscal.data.abstract) have to match their code with the "in"
    and "not in" operators too."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cfop_model = cls.env["l10n_br_fiscal.cfop"]
        cls.cfop_5101 = cls.env.ref("l10n_br_fiscal.cfop_5101")
        cls.cfop_5102 = cls.env.ref("l10n_br_fiscal.cfop_5102")

    def test_many2one_search_by_code(self):
        """5101 and 5102 both have 1102 as inverse CFOP."""
        cfops = self.cfop_model.search([("cfop_inverse_id", "=", "1102")])
        self.assertIn(self.cfop_5101, cfops)
        self.assertIn(self.cfop_5102, cfops)

    def test_many2one_search_by_code_negative(self):
        """5101 returns with 1201 and 5102 with 1202."""
        cfops = self.cfop_model.search([("cfop_return_id", "!=", "1202")])
        self.assertIn(self.cfop_5101, cfops)
        self.assertNotIn(self.cfop_5102, cfops)

    def test_display_name_in(self):
        cfops = self.cfop_model.search([("display_name", "in", ["5102"])])
        self.assertEqual(cfops, self.cfop_5102)
