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


class TestResPartnerDocumentTagChoice(TransactionCase):
    """The NFe CNPJ/CPF tag follows the actual document (its length),
    not is_company, and a delivery address without a document inherits
    the Brazilian parent partner's one."""

    def test_tag_follows_document_not_is_company(self):
        """A pessoa física carrying a CNPJ (e.g. produtor rural, #5580)
        exports the CNPJ tag even with is_company=False."""
        cnpj = "48290617000115"
        partner = self.env["res.partner"].create(
            {
                "name": "PF carrying a CNPJ",
                "is_company": False,
                "vat": cnpj,
                "country_id": self.env.ref("base.br").id,
            }
        )
        self.assertEqual(partner.nfe40_choice_dest, "nfe40_CNPJ")
        self.assertEqual(partner.nfe40_choice_tlocal, "nfe40_CNPJ")
        self.assertEqual(partner.nfe40_CNPJ, cnpj)
        self.assertFalse(partner.nfe40_CPF)

    def test_delivery_address_inherits_parent_document(self):
        parent = self.env.ref("l10n_br_base.res_partner_cliente1_sp")
        child = self.env["res.partner"].create(
            {
                "name": "Delivery address without document",
                "parent_id": parent.id,
                "type": "delivery",
                "country_id": self.env.ref("base.br").id,
                "state_id": parent.state_id.id,
                "city_id": parent.city_id.id,
                "zip": parent.zip,
            }
        )
        self.assertFalse(child.vat)
        self.assertEqual(child.nfe40_CNPJ, parent.cnpj_cpf_stripped)
        self.assertEqual(child.nfe40_choice_tlocal, "nfe40_CNPJ")
        self.assertFalse(child.nfe40_CPF)

    def test_delivery_address_inherits_parent_cpf(self):
        parent = self.env["res.partner"].create(
            {
                "name": "PF parent",
                "is_company": False,
                "vat": "71533482632",
                "country_id": self.env.ref("base.br").id,
            }
        )
        child = self.env["res.partner"].create(
            {
                "name": "Delivery address without document",
                "parent_id": parent.id,
                "type": "delivery",
                "country_id": self.env.ref("base.br").id,
            }
        )
        self.assertEqual(child.nfe40_CPF, "71533482632")
        self.assertEqual(child.nfe40_choice_tlocal, "nfe40_CPF")
        self.assertFalse(child.nfe40_CNPJ)

    def test_no_inherit_from_foreign_parent(self):
        foreign = self.env["res.partner"].create(
            {
                "name": "Foreign Co",
                "is_company": True,
                "vat": "US12345",
                "country_id": self.env.ref("base.us").id,
            }
        )
        child = self.env["res.partner"].create(
            {
                "name": "Foreign delivery address",
                "parent_id": foreign.id,
                "type": "delivery",
                "country_id": self.env.ref("base.us").id,
            }
        )
        self.assertFalse(child.nfe40_CNPJ)
        self.assertFalse(child.nfe40_CPF)
