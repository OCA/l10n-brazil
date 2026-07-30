# Copyright (C) 2026 - Antônio S. Pereira Neto - Engenere <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase


class DuplicateCnpjTest(TransactionCase):
    """The same CNPJ must not be registered twice, regardless of the
    formatting that was typed.

    Regression for OCA/l10n-brazil#4430: ``_check_cnpj_l10n_br_ie_code``
    compared the already formatted ``vat`` (so "06.990.590/0001-23" !=
    "06.990.590/000123") and, on top of that, a misplaced ``return`` killed the
    check entirely. The correct comparison is by the normalized
    ``cnpj_cpf_stripped`` value.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # allow_cnpj_multi_ie OFF: the settings field represents "off" by
        # removing the parameter (set_param deletes on a False bool), so the
        # default is strict and any duplicate CNPJ is blocked regardless of IE.
        cls.env["ir.config_parameter"].sudo().set_param(
            "l10n_br_base.allow_cnpj_multi_ie", False
        )
        # Real (valid) CNPJ of Google Brasil, used as an example.
        cls.google_cnpj = "06.990.590/0001-23"
        cls.google_cnpj_unformatted = "06.990.590/000123"
        # Another valid and distinct CNPJ, for the negative case.
        cls.other_cnpj = "02.960.895/0001-31"

        cls.partner_model = cls.env["res.partner"].with_context(tracking_disable=True)
        cls.base_vals = {
            "is_company": True,
            "country_id": cls.env.ref("base.br").id,
            "state_id": cls.env.ref("base.state_br_es").id,
            "city_id": cls.env.ref("l10n_br_base.city_3205002").id,
        }

    def _create_partner(self, name, vat):
        return self.partner_model.create(dict(self.base_vals, name=name, vat=vat))

    def test_dup_same_format(self):
        """Case 1: same CNPJ, same formatting -> ValidationError."""
        self._create_partner("Google 1", self.google_cnpj)
        with self.assertRaises(ValidationError):
            self._create_partner("Google 2", self.google_cnpj)

    def test_dup_different_format(self):
        """Case 2 (the bug): same CNPJ, different formatting -> ValidationError."""
        self._create_partner("Google 1", self.google_cnpj)
        with self.assertRaises(ValidationError):
            self._create_partner("Google 2", self.google_cnpj_unformatted)

    def test_distinct_cnpj_allowed(self):
        """A distinct CNPJ must not be blocked (guard against false positives)."""
        self._create_partner("Google 1", self.google_cnpj)
        partner = self._create_partner("Other Co", self.other_cnpj)
        self.assertTrue(partner.id, "A partner with a distinct CNPJ should be created.")

    def _create_partner_with_ie(self, name, vat, ie):
        # disable_ie_validation keeps the test focused on the duplicate/IE
        # branch instead of state-wise IE checksums (covered by test_other_ie).
        return self.partner_model.with_context(disable_ie_validation=True).create(
            dict(self.base_vals, name=name, vat=vat, l10n_br_ie_code=ie)
        )

    def test_multi_ie_allows_different_ie(self):
        """With allow_cnpj_multi_ie enabled, the same CNPJ under a *different*
        State Tax Number is allowed (multi-establishment scenario)."""
        self.env["ir.config_parameter"].sudo().set_param(
            "l10n_br_base.allow_cnpj_multi_ie", True
        )
        self._create_partner_with_ie("Branch 1", self.google_cnpj, "111111111")
        partner = self._create_partner_with_ie(
            "Branch 2", self.google_cnpj, "222222222"
        )
        self.assertTrue(partner.id, "Same CNPJ with a distinct IE should be allowed.")

    def test_multi_ie_blocks_same_ie(self):
        """With allow_cnpj_multi_ie enabled, the same CNPJ under the *same*
        State Tax Number is still blocked."""
        self.env["ir.config_parameter"].sudo().set_param(
            "l10n_br_base.allow_cnpj_multi_ie", True
        )
        self._create_partner_with_ie("Branch 1", self.google_cnpj, "111111111")
        with self.assertRaises(ValidationError):
            self._create_partner_with_ie("Branch 2", self.google_cnpj, "111111111")

    def _desync_stripped(self, partner):
        """Reproduce the effect of a raw SQL write on ``vat``.

        ``cnpj_cpf_stripped`` is a stored computed field, so a plain UPDATE
        (a data migration, a bulk import) leaves it behind. This is the state
        the 16.0.2.0.0 pre-migration left on every record it touched.
        """
        # Flush first: right after create the computed value is still pending,
        # and the ORM would write it back over the raw UPDATE below.
        partner.flush_recordset(["cnpj_cpf_stripped"])
        self.env.cr.execute(
            "UPDATE res_partner SET cnpj_cpf_stripped = NULL WHERE id = %s",
            (partner.id,),
        )
        partner.invalidate_recordset(["cnpj_cpf_stripped"])
        self.assertFalse(
            partner.cnpj_cpf_stripped, "setup failed: the field is still in sync"
        )

    def test_out_of_sync_stripped_is_not_a_duplicate(self):
        """Records with an out-of-sync ``cnpj_cpf_stripped`` and *distinct*
        CNPJs must not be reported as duplicates of each other.

        Before the fix the domain was built from the stored (empty) value, so
        it became ("cnpj_cpf_stripped", "=", False) and matched every other
        out-of-sync record -- flagging a completely unrelated partner.
        """
        first = self._create_partner("Google", self.google_cnpj)
        second = self._create_partner("Other Co", self.other_cnpj)
        self._desync_stripped(first)
        self._desync_stripped(second)

        # Must not raise: the two hold different CNPJs.
        second._check_cnpj_l10n_br_ie_code()

    def test_out_of_sync_stripped_still_detects_duplicate(self):
        """A real duplicate is still caught when the stored value is empty,
        because the comparison normalizes from ``vat`` itself."""
        original = self._create_partner("Google 1", self.google_cnpj)
        # allow_vat_duplicate bypasses the check on create so the test can set
        # up the duplicate it wants to assert on.
        duplicate = self.partner_model.with_context(allow_vat_duplicate=True).create(
            dict(self.base_vals, name="Google 2", vat=self.google_cnpj)
        )
        self._desync_stripped(duplicate)

        # Drop allow_vat_duplicate before asserting: the recordset carries the
        # context it was created with, and the check bails out early on it.
        with self.assertRaises(ValidationError) as capture:
            duplicate.with_context(
                allow_vat_duplicate=False
            )._check_cnpj_l10n_br_ie_code()

        # Assert *which* record is reported. Raising alone is not enough: with
        # the old code the empty domain matched any record with an empty stored
        # value, so the error was raised for the wrong partner.
        self.assertIn(original.name, capture.exception.args[0])

    def test_tax_exempt_partners_are_not_duplicates(self):
        """Two partners "not subject to tax" are not duplicates of each other.

        ``base`` documents ``vat = "/"`` as "the partner is not subject to
        tax", and ``_compute_cnpj_cpf_stripped`` only keeps alphanumeric
        characters, so the stored document is legitimately an empty string --
        with the compute perfectly in sync, no raw SQL write involved. Without
        the guard the clause degrades to ("cnpj_cpf_stripped", "=", "") and
        every other tax-exempt partner matches.

        Note this is a distinct state from a partner with no ``vat`` at all,
        which stores NULL and is therefore never matched by that clause.
        """
        # is_company=False: for a document that is not a valid CNPJ, the check
        # only reports duplicates on individuals (the CPF/RG branch).
        exempt_vals = {
            "is_company": False,
            "country_id": self.env.ref("base.us").id,
            "vat": "/",
        }
        self.partner_model.create(dict(exempt_vals, name="Tax exempt 1"))
        second = self.partner_model.create(dict(exempt_vals, name="Tax exempt 2"))

        # Must not raise, neither on the create above nor on an explicit
        # re-check.
        second._check_cnpj_l10n_br_ie_code()
