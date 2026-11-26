# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase

from ..tools import domain_field_codes

# (CEST code, NCM) pairs of the shipped table that still match no NCM: the NCM table has
# no 9018.9x or 9269 line. Everything else must match, so a code that lost its leading
# zero (4029 for 0402.9) or names a subheading the NCM table splits (02109900) fails.
KNOWN_WITHOUT_NCM = {("13.016.00", "901891"), ("20.040.00", "9269090")}


class TestCest(TransactionCase):
    def test_every_ncm_of_a_cest_matches_an_ncm(self):
        ncm = self.env["l10n_br_fiscal.ncm"]
        unmatched = set()
        for cest in self.env["l10n_br_fiscal.cest"].search([("ncms", "!=", False)]):
            for token in cest.ncms.replace(" ", "").replace(";", ",").split(","):
                if not token or "_" in token:
                    continue
                domain = domain_field_codes(field_codes=token)
                if domain and not ncm.search_count(domain):
                    unmatched.add((cest.code, token.replace(".", "")))
        self.assertEqual(unmatched - KNOWN_WITHOUT_NCM, set())

    def test_a_cest_without_leading_zero_finds_its_ncm(self):
        cest = self.env.ref("l10n_br_fiscal.cest_1702000")
        self.assertEqual(cest.ncms, "04029")
        self.assertTrue(cest.ncm_ids)
        codes = cest.ncm_ids.mapped("code_unmasked")
        self.assertTrue(all(c.startswith("04029") for c in codes))
