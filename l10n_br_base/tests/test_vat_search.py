# Copyright (C) 2026-Today - Akretion (<https://www.akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class VatSearchTest(TransactionCase):
    """Partners must be searchable by VAT with or without punctuation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "VAT Search Test Company",
                "is_company": True,
                "country_id": cls.env.ref("base.br").id,
                "vat": "56.647.352/0001-98",
            }
        )

    def test_vat_stored_unformatted(self):
        self.assertEqual(self.partner.vat, "56647352000198")

    def test_search_vat_formatted(self):
        matches = self.env["res.partner"].search(
            [("vat", "ilike", "56.647.352/0001-98")]
        )
        self.assertIn(self.partner, matches)

    def test_search_vat_unformatted(self):
        matches = self.env["res.partner"].search([("vat", "ilike", "56647352000198")])
        self.assertIn(self.partner, matches)

    def test_search_vat_partial_formatted(self):
        matches = self.env["res.partner"].search([("vat", "ilike", "56.647.352")])
        self.assertIn(self.partner, matches)

    def test_search_count_vat_formatted(self):
        count = self.env["res.partner"].search_count(
            [("vat", "ilike", "56.647.352/0001-98")]
        )
        self.assertGreaterEqual(count, 1)

    def test_no_stripped_match_context(self):
        matches = (
            self.env["res.partner"]
            .with_context(no_stripped_match=True)
            .search([("vat", "ilike", "56.647.352/0001-98")])
        )
        self.assertNotIn(self.partner, matches)
