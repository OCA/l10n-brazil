# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

from datetime import datetime

from odoo.tests import TransactionCase


class SpedDocumentCommon:
    @staticmethod
    def _access_key(number, cnpj="49190159000105", when=None):
        """A valid 44 digits access key (check digit included) for the number,
        with the year and month of the document (the NF-e checks them)."""
        yymm = (when or datetime(2026, 7, 20)).strftime("%y%m")
        base = f"35{yymm}{cnpj}55001{number.zfill(9)}1{number.zfill(8)}"
        weights = [2, 3, 4, 5, 6, 7, 8, 9]
        total = sum(
            int(digit) * weights[index % 8]
            for index, digit in enumerate(reversed(base))
        )
        check = 11 - total % 11
        return base + str(0 if check >= 10 else check)

    @classmethod
    def _sped_document(cls, number, operation="fo_compras", **vals):
        """A fiscal document as the books read it: an entry from the supplier
        by default, an outgoing one with ``operation="fo_venda"``."""
        ref = cls.env.ref
        fiscal_operation = ref(f"l10n_br_fiscal.{operation}")
        operation_type = fiscal_operation.fiscal_operation_type
        values = {
            "company_id": ref("l10n_br_base.empresa_lucro_presumido").id,
            "fiscal_operation_id": fiscal_operation.id,
            "fiscal_operation_type": operation_type,
            "document_type_id": ref("l10n_br_fiscal.document_55").id,
            "document_number": str(number),
            "document_serie": "1",
            "issuer": "partner" if operation_type == "in" else "company",
            "partner_id": ref("l10n_br_base.res_partner_cliente1_sp").id,
            "document_date": datetime(2026, 7, 20, 12, 0),
            "date_in_out": datetime(2026, 7, 20, 12, 0),
            "state_edoc": "autorizada",
        }
        values.update(vals)
        if "document_key" not in vals:
            values["document_key"] = cls._access_key(
                str(number), when=values["document_date"]
            )
        return cls.env["l10n_br_fiscal.document"].create(values)


class TestSpedDocument(SpedDocumentCommon, TransactionCase):
    """The rules of the fiscal document that every SPED shares."""

    def test_cod_sit_follows_the_state_of_the_document(self):
        expected = {
            "autorizada": "00",
            "cancelada": "02",
            "denegada": "04",
            "inutilizada": "05",
        }
        for number, (state, cod_sit) in enumerate(expected.items(), 1):
            doc = self._sped_document(number, state_edoc=state)
            self.assertEqual(doc._get_sped_cod_sit(), cod_sit, state)

    def test_cod_sit_of_a_complementary_document(self):
        doc = self._sped_document(11)
        doc.edoc_purpose = "2"
        self.assertEqual(doc._get_sped_cod_sit(), "06")

    def test_cod_sit_written_on_the_document_wins(self):
        doc = self._sped_document(12, state_fiscal="08")
        self.assertEqual(doc._get_sped_cod_sit(), "08")

    def test_denied_and_unused_notes_have_no_c100(self):
        """The codes 04 and 05 left the Guia Pratico in 01/2023: a denied note
        and an unused number are not booked; a cancelled one still is."""
        expected = {
            "autorizada": True,
            "cancelada": True,
            "denegada": False,
            "inutilizada": False,
        }
        for number, (state, has_c100) in enumerate(expected.items(), 21):
            doc = self._sped_document(number, state_edoc=state)
            self.assertEqual(doc._has_sped_c100(), has_c100, state)

    def test_cancelled_denied_and_unused_carry_no_values(self):
        self.assertFalse(self._sped_document(31)._is_sped_cancelled())
        for number, state in enumerate(("cancelada", "denegada", "inutilizada"), 32):
            doc = self._sped_document(number, state_edoc=state)
            self.assertTrue(doc._is_sped_cancelled(), state)

    def test_document_without_installments_is_without_payment(self):
        self.assertEqual(self._sped_document(41)._get_sped_ind_pgto(), "9")

    def test_nfe_without_access_key(self):
        self.assertFalse(self._sped_document(51)._is_sped_without_access_key())
        self.assertTrue(
            self._sped_document(52, document_key=False)._is_sped_without_access_key()
        )
        other_model = self._sped_document(
            53,
            document_key=False,
            document_type_id=self.env.ref("l10n_br_fiscal.document_01").id,
        )
        self.assertFalse(other_model._is_sped_without_access_key())

    def test_entry_date_is_never_before_the_emission(self):
        later = self._sped_document(61, date_in_out=datetime(2026, 7, 25, 12, 0))
        self.assertEqual(later._get_sped_entry_date(), later.date_in_out)
        earlier = self._sped_document(62, date_in_out=datetime(2026, 7, 5, 12, 0))
        self.assertEqual(earlier._get_sped_entry_date(), earlier.document_date)
        missing = self._sped_document(63, date_in_out=False)
        self.assertEqual(missing._get_sped_entry_date(), missing.document_date)

    def test_own_issue_is_the_nfe_issued_by_the_company(self):
        self.assertTrue(
            self._sped_document(71, operation="fo_venda")._is_sped_own_issue()
        )
        self.assertFalse(self._sped_document(72)._is_sped_own_issue())

    def test_cod_part_is_the_id_of_the_partner(self):
        partner = self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        self.assertEqual(partner._get_sped_cod_part(), str(partner.id))
