# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestNFCeResPartner(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_id = cls.env.ref("l10n_br_base.res_partner_kmee")
        cls.partner_id.is_anonymous_consumer = True

    def test_compute_fields(self):
        self.partner_id._compute_nfe40_ender()

        self.assertFalse(self.partner_id.nfe40_xLgr)
        self.assertFalse(self.partner_id.nfe40_nro)
        self.assertFalse(self.partner_id.nfe40_xCpl)
        self.assertFalse(self.partner_id.nfe40_xBairro)
        self.assertFalse(self.partner_id.nfe40_cMun)
        self.assertFalse(self.partner_id.nfe40_xMun)
        self.assertFalse(self.partner_id.nfe40_UF)
        self.assertFalse(self.partner_id.nfe40_cPais)
        self.assertFalse(self.partner_id.nfe40_xPais)


class TestResPartnerMatchOrCreateM2o(TransactionCase):
    def test_match_or_create_m2o_cpf_only_carrier_not_duplicated(self):
        """A carrier (``transporta``) identified only by CPF must be
        matched on a second import instead of being created again."""
        partner_model = self.env["res.partner"]
        cpf = "11144477735"

        def carrier_vals():
            return {
                "nfe40_CPF": cpf,
                "nfe40_xNome": "Transportador Autonomo",
                "is_company": False,
                "country_id": self.env.ref("base.br").id,
            }

        partner_id_1 = partner_model.match_or_create_m2o(carrier_vals(), {})
        partner_id_2 = partner_model.match_or_create_m2o(carrier_vals(), {})

        self.assertEqual(
            partner_id_1,
            partner_id_2,
            "Importing the same CPF-only carrier twice must reuse the "
            "existing partner instead of creating a duplicate.",
        )
        self.assertEqual(partner_model.search_count([("vat", "=", cpf)]), 1)
