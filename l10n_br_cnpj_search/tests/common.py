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

        cls.mocked_response_serpro_1 = {
            "ni": "34238864000168",
            "nomeEmpresarial": "UHIEQKX WHNHIWD NH  FIXKHUUWPHMVX NH NWNXU (UHIFIX)",
            "nomeFantasia": "UHIFIX UHNH",
            "telefones": [
                {"ddd": "61", "numero": "22222222"},
                {"ddd": "61", "numero": "22222222"},
            ],
            "cep": "70836900",
            "correioEletronico": "EMPRESA@XXXXXX.BR",
            "socios": [
                {
                    "tipoSocio": "2",
                    "cpf": "07119488449",
                    "nome": "LUIZA ARAUJO DE OLIVEIRA",
                    "qualificacao": "49",
                    "dataInclusao": "2014-01-01",
                    "pais": {"codigo": "105", "descricao": "BRASIL"},
                    "representanteLegal": {
                        "cpf": "00000000000",
                        "nome": "",
                        "qualificacao": "00",
                    },
                },
                {
                    "tipoSocio": "2",
                    "cpf": "23982012600",
                    "nome": "JOANA ALVES MUNDIM PENA",
                    "qualificacao": "49",
                    "dataInclusao": "2014-01-01",
                    "pais": {"codigo": "105", "descricao": "BRASIL"},
                    "representanteLegal": {
                        "cpf": "00000000000",
                        "nome": "",
                        "qualificacao": "00",
                    },
                },
                {
                    "tipoSocio": "2",
                    "cpf": "13946994415",
                    "nome": "LUIZA BARBOSA BEZERRA",
                    "qualificacao": "49",
                    "dataInclusao": "2014-01-01",
                    "pais": {"codigo": "105", "descricao": "BRASIL"},
                    "representanteLegal": {
                        "cpf": "00000000000",
                        "nome": "",
                        "qualificacao": "00",
                    },
                },
                {
                    "tipoSocio": "2",
                    "cpf": "00031298702",
                    "nome": "MARCELO ANTONIO BARROS DE CICCO",
                    "qualificacao": "49",
                    "dataInclusao": "2014-01-01",
                    "pais": {"codigo": "105", "descricao": "BRASIL"},
                    "representanteLegal": {
                        "cpf": "00000000000",
                        "nome": "",
                        "qualificacao": "00",
                    },
                },
                {
                    "tipoSocio": "2",
                    "cpf": "76822320300",
                    "nome": "LUIZA ALDENORA",
                    "qualificacao": "49",
                    "dataInclusao": "2014-01-01",
                    "pais": {"codigo": "105", "descricao": "BRASIL"},
                    "representanteLegal": {
                        "cpf": "00000000000",
                        "nome": "",
                        "qualificacao": "00",
                    },
                },
            ],
            "endereco": {
                "tipoLogradouro": "SETOR",
                "logradouro": "NH BIWMNH WIHW MXIVH",
                "numero": "Q.601",
                "complemento": "LOTE V",
                "cep": "70836900",
                "bairro": "ASA NORTE",
                "municipio": {"codigo": "9701", "descricao": "BRASILIA"},
                "uf": "DF",
                "pais": {"codigo": "105", "descricao": "BRASIL"},
            },
            "naturezaJuridica": {"codigo": "2011", "descricao": "Empresa Pública"},
            "capitalSocial": 0,
            "cnaePrincipal": {
                "codigo": "6204000",
                "descricao": "Consultoria em tecnologia da informação",
            },
        }

        cls.mocked_response_serpro_2 = {
            "ni": "34238864000249",
            "nomeEmpresarial": "UHIEQKX WHNHIWD NH  FIXKHUUWPHMVX NH NWNXU (UHIFIX)",
            "nomeFantasia": "UHIFIX UHNH",
            "telefones": [
                {"ddd": "61", "numero": "22222222"},
                {"ddd": "61", "numero": "22222222"},
            ],
            "cep": "70836900",
            "correioEletronico": "EMPRESA@XXXXXX.BR",
            "socios": [
                {
                    "tipoSocio": "2",
                    "cpf": "07119488449",
                    "nome": "LUIZA ARAUJO DE OLIVEIRA",
                    "qualificacao": "49",
                    "dataInclusao": "2014-01-01",
                    "pais": {"codigo": "105", "descricao": "BRASIL"},
                    "representanteLegal": {
                        "cpf": "00000000000",
                        "nome": "",
                        "qualificacao": "00",
                    },
                },
                {
                    "tipoSocio": "2",
                    "cpf": "23982012600",
                    "nome": "JOANA ALVES MUNDIM PENA",
                    "qualificacao": "49",
                    "dataInclusao": "2014-01-01",
                    "pais": {"codigo": "105", "descricao": "BRASIL"},
                    "representanteLegal": {
                        "cpf": "00000000000",
                        "nome": "",
                        "qualificacao": "00",
                    },
                },
                {
                    "tipoSocio": "2",
                    "cpf": "13946994415",
                    "nome": "LUIZA BARBOSA BEZERRA",
                    "qualificacao": "49",
                    "dataInclusao": "2014-01-01",
                    "pais": {"codigo": "105", "descricao": "BRASIL"},
                    "representanteLegal": {
                        "cpf": "00000000000",
                        "nome": "",
                        "qualificacao": "00",
                    },
                },
                {
                    "tipoSocio": "2",
                    "cpf": "00031298702",
                    "nome": "MARCELO ANTONIO BARROS DE CICCO",
                    "qualificacao": "49",
                    "dataInclusao": "2014-01-01",
                    "pais": {"codigo": "105", "descricao": "BRASIL"},
                    "representanteLegal": {
                        "cpf": "00000000000",
                        "nome": "",
                        "qualificacao": "00",
                    },
                },
                {
                    "tipoSocio": "2",
                    "cpf": "76822320300",
                    "nome": "LUIZA ALDENORA",
                    "qualificacao": "49",
                    "dataInclusao": "2014-01-01",
                    "pais": {"codigo": "105", "descricao": "BRASIL"},
                    "representanteLegal": {
                        "cpf": "00000000000",
                        "nome": "",
                        "qualificacao": "00",
                    },
                },
            ],
            "endereco": {
                "tipoLogradouro": "SETOR",
                "logradouro": "NH BIWMNH WIHW MXIVH",
                "numero": "Q.601",
                "complemento": "LOTE V",
                "cep": "70836900",
                "bairro": "ASA NORTE",
                "municipio": {"codigo": "9701", "descricao": "BRASILIA"},
                "uf": "DF",
                "pais": {"codigo": "105", "descricao": "BRASIL"},
            },
            "naturezaJuridica": {"codigo": "2011", "descricao": "Empresa Pública"},
            "capitalSocial": 0,
            "cnaePrincipal": {
                "codigo": "6204000",
                "descricao": "Consultoria em tecnologia da informação",
            },
        }

        cls.mocked_response_serpro_3 = {
            "nomeEmpresarial": "UHIEQKX WHNHIWD NH  FIXKHUUWPHMVX NH NWNXU (UHIFIX)",
            "nomeFantasia": "UHIFIX UHNH",
            "telefones": [
                {"ddd": "61", "numero": "22222222"},
                {"ddd": "61", "numero": "22222222"},
            ],
            "cep": "70836900",
            "correioEletronico": "EMPRESA@XXXXXX.BR",
            "socios": [
                {
                    "tipoSocio": "2",
                    "nome": "LUIZA ARAUJO DE OLIVEIRA",
                    "qualificacao": "49",
                    "pais": {"codigo": "105", "descricao": "BRASIL"},
                    "representanteLegal": {"nome": "", "qualificacao": "00"},
                },
                {
                    "tipoSocio": "2",
                    "nome": "JOANA ALVES MUNDIM PENA",
                    "qualificacao": "49",
                    "pais": {"codigo": "105", "descricao": "BRASIL"},
                    "representanteLegal": {"nome": "", "qualificacao": "00"},
                },
                {
                    "tipoSocio": "2",
                    "nome": "LUIZA BARBOSA BEZERRA",
                    "qualificacao": "49",
                    "pais": {"codigo": "105", "descricao": "BRASIL"},
                    "representanteLegal": {"nome": "", "qualificacao": "00"},
                },
                {
                    "tipoSocio": "2",
                    "nome": "MARCELO ANTONIO BARROS DE CICCO",
                    "qualificacao": "49 ",
                    "pais": {"codigo": "105", "descricao": "BRASIL"},
                    "representanteLegal": {"nome": "", "qualificacao": "00"},
                },
                {
                    "tipoSocio": "2",
                    "nome": "LUIZA ALDENORA",
                    "qualificacao": "49",
                    "pais": {"codigo": "105", "descricao": "BRASIL"},
                    "representanteLegal": {"nome": "", "qualificacao": "00"},
                },
            ],
            "endereco": {
                "tipoLogradouro": "SETOR",
                "logradouro": "NH BIWMNH WIHW MXIVH",
                "numero": "Q.601",
                "complemento": "LOTE V",
                "cep": "70836900",
                "bairro": "ASA NORTE",
                "municipio": {"codigo": "9701", "descricao": "BRASILIA"},
                "uf": "DF",
                "pais": {"codigo": "105", "descricao": "BRASIL"},
            },
            "naturezaJuridica": {"codigo": "2011", "descricao": "Empresa Pública"},
            "capitalSocial": 0,
            "cnaePrincipal": {
                "codigo": "6204000",
                "descricao": "Consultoria em tecnologia da informação",
            },
        }

    @classmethod
    def set_param(cls, param_name, param_value):
        (
            cls.env["ir.config_parameter"]
            .sudo()
            .set_param("l10n_br_cnpj_search." + param_name, param_value)
        )
