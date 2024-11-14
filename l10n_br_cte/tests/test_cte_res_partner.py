# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from erpbrasil.base.fiscal import cnpj_cpf
from erpbrasil.base.misc import format_zipcode

from odoo.tests import TransactionCase


class TestCTeResPartner(TransactionCase):
    def setUp(self):
        super().setUp()

        self.partner_id = self.env.ref("l10n_br_base.res_partner_kmee")

    def test_compute_fields(self):
        self.partner_id.country_id = self.env.ref("base.us")

        self.assertEqual(self.partner_id.cte40_choice_toma, "cte40_idEstrangeiro")
        self.assertEqual(self.partner_id.cte40_cPais, self.env.ref("base.us").bc_code)

    def test_inverse_fields(self):
        # self.partner_id.cte40_idEstrangeiro = "999999999999"
        # self.assertEqual(self.partner_id.vat, self.partner_id.cte40_idEstrangeiro)

        self.partner_id.cte40_CNPJ = "97414612000162"
        self.assertEqual(
            self.partner_id.cnpj_cpf, cnpj_cpf.formata(self.partner_id.cte40_CNPJ)
        )

        self.partner_id.cte40_CPF = "48737433032"
        self.assertEqual(
            self.partner_id.cnpj_cpf, cnpj_cpf.formata(self.partner_id.cte40_CPF)
        )

        self.partner_id.cte40_IE = "630514648079"
        self.assertEqual(self.partner_id.inscr_est, self.partner_id.cte40_IE)

        self.partner_id.cte40_CEP = "04324240"
        self.assertEqual(self.partner_id.zip, format_zipcode(self.partner_id.cte40_CEP))

        self.partner_id.cte40_fone = "(99) 9999-9999"
        self.assertEqual(self.partner_id.phone, self.partner_id.cte40_fone)

        self.partner_id.cte40_cPais = "1058"
        self.partner_id.cte40_UF = "SP"
        self.partner_id.cte40_cMun = "3550308"
        self.assertEqual(
            self.partner_id.country_id.bc_code, self.partner_id.cte40_cPais
        )
        self.assertEqual(self.partner_id.state_id.code, self.partner_id.cte40_UF)
        self.assertEqual(self.partner_id.city_id.ibge_code, self.partner_id.cte40_cMun)

        self.partner_id.cte40_xLgr = "TESTE"
        self.assertEqual(self.partner_id.street_name, self.partner_id.cte40_xLgr)

        self.partner_id.cte40_nro = "999"
        self.assertEqual(self.partner_id.street_number, self.partner_id.cte40_nro)

        self.partner_id.cte40_xCpl = "TESTE"
        self.assertEqual(self.partner_id.street2, self.partner_id.cte40_xCpl)

        self.partner_id.cte40_xBairro = "TESTE"
        self.assertEqual(self.partner_id.district, self.partner_id.cte40_xBairro)
