# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from erpbrasil.base.fiscal import cnpj_cpf
from erpbrasil.base.misc import format_zipcode

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase


class TestMDFeResPartner(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_id = cls.env.ref("l10n_br_base.res_partner_kmee")

    def test_compute_fields(self):
        self.partner_id.country_id = self.env.ref("base.us")

        self.assertEqual(
            self.partner_id.mdfe30_choice_tcontractor, "mdfe30_idEstrangeiro"
        )
        self.assertEqual(self.partner_id.mdfe30_idEstrangeiro, self.partner_id.cnpj_cpf)

    def test_inverse_fields(self):
        foreign_partner = self.env.ref("base.res_partner_12")
        foreign_partner.mdfe30_idEstrangeiro = "999999999999"
        self.assertEqual(foreign_partner.vat, foreign_partner.mdfe30_idEstrangeiro)

        self.partner_id.mdfe30_CNPJ = "97414612000162"
        self.assertEqual(
            self.partner_id.cnpj_cpf, cnpj_cpf.formata(self.partner_id.mdfe30_CNPJ)
        )

        self.partner_id.mdfe30_CPF = "48737433032"
        self.assertEqual(
            self.partner_id.cnpj_cpf, cnpj_cpf.formata(self.partner_id.mdfe30_CPF)
        )

        self.partner_id.mdfe30_IE = "630514648079"
        self.assertEqual(self.partner_id.l10n_br_ie_code, self.partner_id.mdfe30_IE)

        self.partner_id.mdfe30_CEP = "04324240"
        self.assertEqual(
            self.partner_id.zip, format_zipcode(self.partner_id.mdfe30_CEP)
        )

        self.partner_id.mdfe30_fone = "(99) 9999-9999"
        self.assertEqual(self.partner_id.phone, self.partner_id.mdfe30_fone)

        self.partner_id.mdfe30_cPais = "1058"
        self.partner_id.mdfe30_UF = "SP"
        self.partner_id.mdfe30_cMun = "3550308"
        self.assertEqual(
            self.partner_id.country_id.bc_code, self.partner_id.mdfe30_cPais
        )
        self.assertEqual(self.partner_id.state_id.code, self.partner_id.mdfe30_UF)
        self.assertEqual(self.partner_id.city_id.ibge_code, self.partner_id.mdfe30_cMun)

        self.partner_id.mdfe30_xLgr = "TESTE"
        self.assertEqual(self.partner_id.street_name, self.partner_id.mdfe30_xLgr)

        self.partner_id.mdfe30_nro = "999"
        self.assertEqual(self.partner_id.street_number, self.partner_id.mdfe30_nro)

        self.partner_id.mdfe30_xCpl = "TESTE"
        self.assertEqual(self.partner_id.street2, self.partner_id.mdfe30_xCpl)

        self.partner_id.mdfe30_xBairro = "TESTE"
        self.assertEqual(self.partner_id.district, self.partner_id.mdfe30_xBairro)

    def test_compute_mdfe30_rntrc(self):
        self.partner_id.rntrc_code = "12345678"
        self.assertEqual(self.partner_id.mdfe30_RNTRC, "12345678")
        self.partner_id.rntrc_code = False
        self.assertFalse(self.partner_id.mdfe30_RNTRC)

    def test_inverse_mdfe30_rntrc(self):
        self.partner_id.mdfe30_RNTRC = "87654321"
        self.assertEqual(self.partner_id.rntrc_code, "87654321")

    def test_inverse_mdfe30_rntrc_invalid(self):
        with self.assertRaises(ValidationError):
            self.partner_id.mdfe30_RNTRC = "123"
        with self.assertRaises(ValidationError):
            self.partner_id.mdfe30_RNTRC = "abcdefgh"

    def test_onchange_condutor_partner_id(self):
        condutor = self.env["l10n_br_mdfe.modal.rodoviario.veiculo.condutor"].new(
            {"partner_id": self.partner_id.id}
        )
        condutor._onchange_partner_id()
        self.assertEqual(
            condutor.mdfe30_xNome,
            self.partner_id.legal_name or self.partner_id.name,
        )
        self.assertEqual(condutor.mdfe30_CPF, self.partner_id.cnpj_cpf)

    def test_get_binding_class_vehicle_owner(self):
        for binding_name in ("mdfe.30.veictracao_prop", "mdfe.30.veicreboque_prop"):
            binding = self.partner_id._get_binding_class(self.env[binding_name])
            self.assertEqual(binding.__name__, "Prop")
