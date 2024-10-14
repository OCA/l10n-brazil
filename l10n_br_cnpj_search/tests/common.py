# Copyright 2022 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestCnpjCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model = cls.env["res.partner"]
        cls.mocked_response_ws_1 = {
            "nome": "Kilian Macedo Melcher 08777131460",
            "fantasia": "Kilian Macedo Melcher 08777131460",
            "email": "kilian.melcher@gmail.com",
            "logradouro": "Rua Luiza Bezerra Motta",
            "complemento": "Bloco E;Apt 302",
            "numero": "950",
            "cep": "58.410-410",
            "bairro": "Catole",
            "uf": "PB",
            "telefone": "(83) 8665-0905",
            "municipio": "CAMPINA GRANDE",
            "natureza_juridica": "213-5 - Empresário (Individual)",
            "capital_social": "3000.00",
            "atividade_principal": [
                {
                    "code": "47.51-2-01",
                    "text": "********",
                }
            ],
        }

        cls.mocked_response_ws_2 = {
            "nome": "ISLA SEMENTES LTDA.",
            "fantasia": "",
            "email": "contabilidade@isla.com.br",
            "logradouro": "AVENIDA SEVERO DULLIUS",
            "complemento": "Bloco E;Apt 302",
            "numero": "124",
            "cep": "90.200-310",
            "bairro": "ANCHIETA",
            "uf": "RS",
            "telefone": "(51) 9852-9561 / (51) 2136-6600",
            "municipio": "PORTO ALEGRE",
            "natureza_juridica": "206-2 - Sociedade Empresária Limitada",
            "capital_social": "10606804.00",
            "atividade_principal": [
                {
                    "code": "46.89-3-99",
                    "text": """Comércio atacadista especializado em outros
                     produtos intermediários não especificados anteriormente""",
                }
            ],
        }

    def set_param(self, param_name, param_value):
        (
            self.env["ir.config_parameter"]
            .sudo()
            .set_param("l10n_br_cnpj_search." + param_name, param_value)
        )
