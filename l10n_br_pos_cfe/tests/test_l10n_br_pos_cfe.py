# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestL10nBrPosCfe(TransactionCase):
    def setUp(self):
        super().setUp()
        self.pos_config = self.env.ref("point_of_sale.pos_config_main")

    def test_pos_config_sweda(self):
        self.pos_config._demo_configure_pos_config_sat_sweda()

        values_to_compare = {
            "cnpj_homologacao": "53.485.215/0001-06",
            "ie_homologacao": "111.072.115.110",
            "cnpj_software_house": "10.615.281/0001-40",
            "sat_path": "/opt/sat/sweda/libSATDLL_Dual_armv7.so",
            "numero_caixa": 1,
            "cod_ativacao": "12345678",
            "assinatura_sat": "SGR-SAT SISTEMA DE GESTAO E RETAGUARDA DO SAT",
        }

        configured_values = {
            "cnpj_homologacao": self.pos_config.cnpj_homologacao,
            "ie_homologacao": self.pos_config.ie_homologacao,
            "cnpj_software_house": self.pos_config.cnpj_software_house,
            "sat_path": self.pos_config.sat_path,
            "numero_caixa": self.pos_config.numero_caixa,
            "cod_ativacao": self.pos_config.cod_ativacao,
            "assinatura_sat": self.pos_config.assinatura_sat,
        }

        self.assertEqual(
            values_to_compare,
            configured_values,
            "Values for Sweda it's not configured properly",
        )
