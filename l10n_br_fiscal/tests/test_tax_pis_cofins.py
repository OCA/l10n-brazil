# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestTaxPisCofinsNcm(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model = cls.env["l10n_br_fiscal.tax.pis.cofins"]
        # NCM codes shipped as data (also present without demo data, which is
        # how the 19.0 CI installs the modules). The table carries several
        # rows for the same 8 digit code (the exception variants), so the
        # assertions compare the matched codes instead of the record sets.
        cls.ncm_a_code = "22030000"
        cls.ncm_b_code = "73239900"
        cls.ncm_c_code = "73269090"

    def _codes(self, record):
        return set(record.ncm_ids.mapped("code_unmasked"))

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
        self.assertEqual(self._codes(record), {self.ncm_a_code, self.ncm_c_code})

    def test_not_in_ncms_excludes_listed_ncms(self):
        record = self._create(ncms="22030000,73239900", not_in_ncms="73239900")
        self.assertEqual(self._codes(record), {self.ncm_a_code})

    def test_write_not_in_ncms_recomputes(self):
        record = self._create(ncms="22030000,73269090")
        self.assertEqual(self._codes(record), {self.ncm_a_code, self.ncm_c_code})
        record.not_in_ncms = "73269090"
        self.assertEqual(self._codes(record), {self.ncm_a_code})

    def test_write_ncm_exception_recomputes(self):
        record = self._create(ncms="73269090")
        self.assertEqual(self._codes(record), {self.ncm_c_code})
        # no NCM of this code has the exception "99", so nothing matches
        record.ncm_exception = "99"
        self.assertFalse(record.ncm_ids)
