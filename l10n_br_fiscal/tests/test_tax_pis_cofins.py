# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestTaxPisCofinsNcm(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model = cls.env["l10n_br_fiscal.tax.pis.cofins"]
        # NCMs available in demo mode (see demo/__init__.py DEMO_NCM)
        cls.ncm_a = cls.env.ref("l10n_br_fiscal.ncm_22030000")
        cls.ncm_b = cls.env.ref("l10n_br_fiscal.ncm_73239900")
        cls.ncm_c = cls.env.ref("l10n_br_fiscal.ncm_73269090")

    def _create(self, **vals):
        vals.setdefault("code", "TEST_PISCOFINS")
        vals.setdefault("name", "Test PIS/COFINS setup")
        return self.model.create(vals)

    def test_not_in_ncms_without_ncms_matches_nothing(self):
        record = self._create(not_in_ncms="73269090")
        self.assertFalse(record.ncm_ids)

    def test_ncm_exception_without_ncms_matches_nothing(self):
        record = self._create(ncm_exception="01")
        self.assertFalse(record.ncm_ids)

    def test_ncms_without_exclusions(self):
        record = self._create(ncms="22030000,73269090")
        self.assertEqual(record.ncm_ids, self.ncm_a | self.ncm_c)

    def test_not_in_ncms_excludes_listed_ncms(self):
        record = self._create(ncms="22030000,73239900", not_in_ncms="73239900")
        self.assertEqual(record.ncm_ids, self.ncm_a)

    def test_write_not_in_ncms_recomputes(self):
        record = self._create(ncms="22030000,73269090")
        self.assertEqual(record.ncm_ids, self.ncm_a | self.ncm_c)
        record.not_in_ncms = "73269090"
        self.assertEqual(record.ncm_ids, self.ncm_a)

    def test_write_ncm_exception_recomputes(self):
        record = self._create(ncms="73269090")
        self.assertEqual(record.ncm_ids, self.ncm_c)
        # no NCM with exception "99" exists, so nothing matches
        record.ncm_exception = "99"
        self.assertFalse(record.ncm_ids)
