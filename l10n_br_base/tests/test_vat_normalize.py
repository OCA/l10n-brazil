# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestVatNormalize(TransactionCase):
    """A Brazilian CNPJ/CPF typed with spaces must be stored unformatted.

    ``_normalize_vat`` used to strip only punctuation (via
    ``erpbrasil.base.misc.punctuation_rm``), which keeps spaces, so a value
    like "264 284 46847" stayed in ``vat`` with its spaces and later broke the
    NF-e schema validation (CPF must match ``[0-9]{11}``).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_model = cls.env["res.partner"].with_context(tracking_disable=True)
        cls.br = cls.env.ref("base.br")

    def test_spaced_cpf_is_stored_unformatted(self):
        partner = self.partner_model.create(
            {"name": "VAT Test", "country_id": self.br.id, "vat": "264 284 46847"}
        )
        self.assertEqual(partner.vat, "26428446847")
        self.assertEqual(partner.cnpj_cpf_stripped, "26428446847")

    def test_spaced_and_punctuated_cnpj_is_stored_unformatted(self):
        partner = self.partner_model.create(
            {
                "name": "VAT Test Co",
                "is_company": True,
                "country_id": self.br.id,
                "state_id": self.env.ref("base.state_br_es").id,
                "city_id": self.env.ref("l10n_br_base.city_3205002").id,
                "vat": "06.990.590 / 0001-23",
            }
        )
        self.assertEqual(partner.vat, "06990590000123")

    def test_write_normalizes_spaced_vat(self):
        partner = self.partner_model.create(
            {"name": "VAT Test", "country_id": self.br.id, "vat": "26428446847"}
        )
        partner.write({"vat": "264 284 468 47"})
        self.assertEqual(partner.vat, "26428446847")
