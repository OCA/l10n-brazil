# Copyright 2022 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase

MOCK_REQUESTS_GET = (
    "odoo.addons.l10n_br_cnpj_search.wizard.partner_cnpj_search_wizard.requests.get"
)

# Minimal valid single page PDF (593 bytes), base64. Reused by the mocks.
_PDF_MINIMO_B64 = (
    "JVBERi0xLjQKMSAwIG9iago8PCAvVHlwZSAvQ2F0YWxvZyAvUGFnZXMgMiAwIFIgPj4KZW5kb2Jq"
    "CjIgMCBvYmoKPDwgL1R5cGUgL1BhZ2VzIC9LaWRzIFszIDAgUl0gL0NvdW50IDEgPj4KZW5kb2Jq"
    "CjMgMCBvYmoKPDwgL1R5cGUgL1BhZ2UgL1BhcmVudCAyIDAgUiAvTWVkaWFCb3ggWzAgMCA1OTUg"
    "ODQyXSAvUmVzb3VyY2VzIDw8IC9Gb250IDw8IC9GMSA1IDAgUiA+PiA+PiAvQ29udGVudHMgNCAw"
    "IFIgPj4KZW5kb2JqCjQgMCBvYmoKPDwgL0xlbmd0aCA2MiA+PgpzdHJlYW0KQlQgL0YxIDE4IFRm"
    "IDYwIDc4MCBUZCAoQ29tcHJvdmFudGUgRXhlbXBsbykgVGogRVQKZW5kc3RyZWFtCmVuZG9iago1"
    "IDAgb2JqCjw8IC9UeXBlIC9Gb250IC9TdWJ0eXBlIC9UeXBlMSAvQmFzZUZvbnQgL0hlbHZldGlj"
    "YSA+PgplbmRvYmoKeHJlZgowIDYKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDA5IDAwMDAw"
    "IG4gCjAwMDAwMDAwNTggMDAwMDAgbiAKMDAwMDAwMDExNSAwMDAwMCBuIAowMDAwMDAwMjQxIDAw"
    "MDAwIG4gCjAwMDAwMDAzNDEgMDAwMDAgbiAKdHJhaWxlcgo8PCAvU2l6ZSA2IC9Sb290IDEgMCBS"
    "ID4+CnN0YXJ0eHJlZgo0MTEKJSVFT0Y="
)


class TestCnpjCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create a Brazilian company and switch user to it
        # This prevents tests from failing if main_company is not Brazilian
        # (which causes VAT propagation to children, breaking the test)
        cls.company_br = cls.env["res.company"].create(
            {
                "name": "Company BR",
                "country_id": cls.env.ref("base.br").id,
            }
        )
        cls.env.user.write(
            {
                "company_ids": [cls.company_br.id],
                "company_id": cls.company_br.id,
            }
        )

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

        # cpfcnpj.com.br - package 6 payload of a Simples Nacional company.
        cls.mocked_response_cpfcnpj_simples = {
            "status": 1,
            "cnpj": "34.238.864/0001-68",
            "tipo": "Matriz",
            "razao": "TOKEN TEST LTDA",
            "fantasia": "TOKEN TEST",
            "capitalSocial": 95000,
            "email": "contato@empresa.com",
            "simplesNacional": {"optante": "Sim", "inicio": "17/01/2020"},
            "simei": {"optante": "Não"},
            "porte": {"id": "03", "descricao": "Empresa de Pequeno Porte"},
            "matrizEndereco": {
                "cep": "39400-000",
                "tipo": "Rua",
                "logradouro": "Rua A",
                "numero": "1",
                "complemento": "Sala 1",
                "bairro": "Centro",
                "cidade": "Montes Claros",
                "uf": "MG",
            },
            "ibge": {
                "estado": {"sigla": "MG", "ibge_id": 31},
                "cidade": {"nome": "Montes Claros", "ibge_id": 3143302},
            },
            "telefones": [
                {"ddd": "11", "numero": "22334454"},
                {"ddd": "11", "numero": "22334455"},
            ],
            "naturezaJuridica": {
                "codigo": "2062",
                "descricao": "Sociedade Empresaria Limitada",
            },
            "cnae": {
                "fiscal": "6202300",
                "descricao": "Desenvolvimento e licenciamento de programas "
                "de computador customizaveis",
                "secundarias": [
                    {"id": "6201501"},
                    {"id": "6204000"},
                ],
            },
        }

        # cpfcnpj.com.br - package 6 payload of an MEI company.
        cls.mocked_response_cpfcnpj_mei = {
            "status": 1,
            "cnpj": "44.356.113/0001-08",
            "tipo": "Matriz",
            "razao": "JOAO DA SILVA 12345678900",
            "fantasia": "",
            "capitalSocial": 5000,
            "email": "mei@empresa.com",
            "simplesNacional": {"optante": "Sim"},
            "simei": {"optante": "Sim", "inicio": "17/01/2023"},
            "porte": {"id": "01", "descricao": "Microempresa"},
            "matrizEndereco": {
                "cep": "39400-000",
                "logradouro": "Rua B",
                "numero": "10",
                "bairro": "Centro",
                "cidade": "Montes Claros",
                "uf": "MG",
            },
            "ibge": {
                "cidade": {"nome": "Montes Claros", "ibge_id": 3143302},
            },
            "telefones": [{"ddd": "38", "numero": "999998888"}],
            "naturezaJuridica": {
                "codigo": "2135",
                "descricao": "Empresario (Individual)",
            },
            "cnae": {"fiscal": "6202300"},
        }

        # cpfcnpj.com.br - package 6 payload of a company under the normal
        # regime (neither Simples nor SIMEI), without an IBGE code (so the city
        # is resolved by name) and without phone numbers.
        cls.mocked_response_cpfcnpj_normal = {
            "status": 1,
            "cnpj": "34.238.864/0001-68",
            "tipo": "Matriz",
            "razao": "REGIME NORMAL LTDA",
            "fantasia": "Normal Test",
            "capitalSocial": 500000,
            "email": "normal@empresa.com",
            "simplesNacional": {"optante": "Não"},
            "simei": {"optante": "Não"},
            "porte": {"id": "05", "descricao": "Demais"},
            "matrizEndereco": {
                "cep": "39400-000",
                "tipo": "Rua",
                "logradouro": "Rua C",
                "numero": "20",
                "bairro": "Centro",
                "cidade": "Montes Claros",
                "uf": "MG",
            },
            "naturezaJuridica": {
                "codigo": "2062",
                "descricao": "Sociedade Empresaria Limitada",
            },
            "cnae": {"fiscal": "6202300"},
        }

        # cpfcnpj.com.br - package 5 payload, which carries no tax regime data,
        # so tax_framework must be left untouched.
        cls.mocked_response_cpfcnpj_package5 = {
            "status": 1,
            "cnpj": "34.238.864/0001-68",
            "tipo": "Matriz",
            "razao": "PACOTE CINCO LTDA",
            "fantasia": "Pacote 5",
            "capitalSocial": 12000,
            "email": "p5@empresa.com",
            "matrizEndereco": {
                "cep": "39400-000",
                "logradouro": "Rua D",
                "numero": "5",
                "bairro": "Centro",
                "cidade": "Montes Claros",
                "uf": "MG",
            },
            "ibge": {"cidade": {"ibge_id": 3143302}},
            "naturezaJuridica": {"codigo": "2062"},
            "cnae": {"fiscal": "6202300"},
        }

        # cpfcnpj.com.br - package 6 payload of an active head office with a
        # full QSA: three partners, one of them a foreign company partner with a
        # legal representative. Values are fictitious.
        cls.mocked_response_cpfcnpj_qsa = {
            "status": 1,
            "cnpj": "13347016000117",
            "cnpj_raiz": "13347016",
            "tipo": "Matriz",
            "razao": "Empresa Exemplo Comercio e Servicos Ltda",
            "fantasia": "Exemplo Servicos",
            "capitalSocial": 3631639.0,
            "inicioAtividade": "14/02/2011",
            "email": "contato@exemplo.com.br",
            "responsavel": None,
            "responsavelCpf": None,
            "responsavelQualificacao": {"id": 16, "descricao": "Presidente"},
            "responsavelFederativo": None,
            "simplesNacional": {
                "optante": "Nao",
                "inicio": None,
                "fim": None,
                "anteriores": [],
                "mei": "Nao",
                "data_opcao_mei": None,
                "data_exclusao_mei": None,
                "atualizado_em": None,
            },
            "matrizEndereco": {
                "cep": "01310100",
                "tipo": "Avenida",
                "logradouro": "das Nacoes",
                "numero": "1000",
                "complemento": "Sala 12",
                "bairro": "Centro",
                "cidade": "Sao Paulo",
                "uf": "SP",
            },
            "ibge": {
                "pais": {
                    "id": "1058",
                    "iso2": "BR",
                    "iso3": "BRA",
                    "nome": "Brasil",
                    "comex_id": "105",
                },
                "estado": {"id": 26, "nome": "Sao Paulo", "sigla": "SP", "ibge_id": 35},
                "cidade": {
                    "id": 9668,
                    "nome": "Sao Paulo",
                    "ibge_id": 3550308,
                    "siafi_id": "7107",
                },
            },
            "matrizfilial": {"id": 1, "tipo": "Matriz"},
            "telefones": [{"ddd": "11", "numero": "40041005"}],
            "fax": {"ddd": None, "numero": None},
            "situacao": {"id": 2, "nome": "Ativa", "data": "14/02/2011", "motivo": []},
            "naturezaJuridica": {
                "codigo": "2062",
                "descricao": "Sociedade Empresaria Limitada",
            },
            "cnae": {
                "fiscal": "7312200",
                "secao": "M",
                "divisao": "73",
                "grupo": "731",
                "classe": "73122",
                "subClasse": "7312200",
                "descricao": "Agenciamento de espacos para publicidade",
                "secundarias": [
                    {
                        "id": 7311400,
                        "descricao": "Servicos de publicidade",
                        "secao": "M",
                        "divisao": "73",
                        "grupo": "731",
                        "classe": "73114",
                        "subclasse": "7311400",
                    }
                ],
            },
            "porte": {"id": "05", "descricao": "Demais"},
            "regimesTributarios": [
                {
                    "ano": 2023,
                    "regime_tributario": "LUCRO PRESUMIDO",
                    "forma_de_tributacao": "Normal",
                    "atualizado_em": "2024-09-01T03:00:00.000Z",
                }
            ],
            "comprovantePdfBase64": _PDF_MINIMO_B64,
            "dispensa": {
                "estabelecimento": None,
                "uf_municipio": None,
                "condicoes": [],
            },
            "socios": [
                {
                    "cpf_cnpj_socio": "111.444.777-35",
                    "nome": "Maria Socia Exemplo",
                    "tipo": "Pessoa Fisica",
                    "data_entrada": "14/02/2011",
                    "cpf_representante_legal": None,
                    "nome_representante": None,
                    "faixa_etaria": "41 a 50 anos",
                    "atualizado_em": "2024-09-01T03:00:00.000Z",
                    "pais_id": "1058",
                    "qualificacao_socio": {"id": 49, "descricao": "Administrador"},
                    "qualificacao_representante": None,
                    "pais": {"id": "1058", "nome": "Brasil"},
                },
                {
                    "cpf_cnpj_socio": "12345678",
                    "nome": "Exemplo Holdings LLC",
                    "tipo": "Pessoa Juridica",
                    "data_entrada": "14/02/2011",
                    "cpf_representante_legal": "222.555.888-46",
                    "nome_representante": "Joao Representante Exemplo",
                    "faixa_etaria": None,
                    "atualizado_em": "2024-09-01T03:00:00.000Z",
                    "pais_id": "249",
                    "qualificacao_socio": {
                        "id": 37,
                        "descricao": "Socio Pessoa Juridica Domiciliado no Exterior",
                    },
                    "qualificacao_representante": "Representante",
                    "pais": {"id": "249", "nome": "ESTADOS UNIDOS"},
                },
                {
                    "cpf_cnpj_socio": "333.666.999-57",
                    "nome": "Carlos Socio Exemplo",
                    "tipo": "Pessoa Fisica",
                    "data_entrada": "14/02/2011",
                    "cpf_representante_legal": None,
                    "nome_representante": None,
                    "faixa_etaria": "51 a 60 anos",
                    "atualizado_em": "2024-09-01T03:00:00.000Z",
                    "pais_id": "1058",
                    "qualificacao_socio": {"id": 49, "descricao": "Administrador"},
                    "qualificacao_representante": None,
                    "pais": {"id": "1058", "nome": "Brasil"},
                },
            ],
            "filiais": [
                {
                    "cnpj": "13347016000200",
                    "tipo": "Filial",
                    "nome_fantasia": None,
                    "situacao_cadastral": "Ativa",
                    "data_inicio_atividade": "10/03/2015",
                }
            ],
            "qsaObservacao": None,
            "pacoteUsado": 6,
            "saldo": 100.0,
            "consultaID": "0000000000000000000000000000000a",
            "delay": 0.42,
        }

        # cpfcnpj.com.br - package 6 payload of a closed company, with a status
        # reason and status date.
        cls.mocked_response_cpfcnpj_baixada = {
            "status": 1,
            "cnpj": "47427653007390",
            "cnpj_raiz": "47427653",
            "tipo": "Matriz",
            "razao": "Empresa Encerrada Exemplo S.A.",
            "fantasia": None,
            "capitalSocial": 500000.0,
            "inicioAtividade": "25/10/2006",
            "email": "financeiro@encerrada-exemplo.com.br",
            "responsavel": None,
            "responsavelCpf": None,
            "responsavelQualificacao": {"id": 10, "descricao": "Diretor"},
            "responsavelFederativo": None,
            "simplesNacional": {
                "optante": "Nao",
                "inicio": None,
                "fim": None,
                "anteriores": [],
                "mei": "Nao",
                "data_opcao_mei": None,
                "data_exclusao_mei": None,
                "atualizado_em": None,
            },
            "matrizEndereco": {
                "cep": "20040002",
                "tipo": "Rua",
                "logradouro": "do Comercio",
                "numero": "200",
                "complemento": None,
                "bairro": "Centro",
                "cidade": "Rio de Janeiro",
                "uf": "RJ",
            },
            "ibge": {
                "estado": {"id": 19, "nome": "Rio de Janeiro", "sigla": "RJ"},
                "cidade": {"nome": "Rio de Janeiro", "ibge_id": 3304557},
            },
            "matrizfilial": {"id": 1, "tipo": "Matriz"},
            "telefones": [{"ddd": "21", "numero": "30030003"}],
            "fax": {"ddd": None, "numero": None},
            "situacao": {
                "id": 8,
                "nome": "Baixada",
                "data": "01/03/2021",
                "motivo": ["Extincao Por Encerramento Liquidacao Voluntaria"],
            },
            "naturezaJuridica": {
                "codigo": "2054",
                "descricao": "Sociedade Anonima Fechada",
            },
            "cnae": {
                "fiscal": "4693100",
                "descricao": "Comercio atacadista de mercadorias em geral",
                "secundarias": [],
            },
            "porte": {"id": "05", "descricao": "Demais"},
            "regimesTributarios": [],
            "comprovantePdfBase64": _PDF_MINIMO_B64,
            "dispensa": {
                "estabelecimento": None,
                "uf_municipio": None,
                "condicoes": [],
            },
            "socios": [
                {
                    "cpf_cnpj_socio": "123.456.780-62",
                    "nome": "Ana Diretora Exemplo",
                    "tipo": "Pessoa Fisica",
                    "data_entrada": "25/10/2006",
                    "cpf_representante_legal": None,
                    "nome_representante": None,
                    "faixa_etaria": "61 a 70 anos",
                    "atualizado_em": "2021-03-01T03:00:00.000Z",
                    "pais_id": "1058",
                    "qualificacao_socio": {"id": 10, "descricao": "Diretor"},
                    "qualificacao_representante": None,
                    "pais": {"id": "1058", "nome": "Brasil"},
                }
            ],
            "filiais": [],
            "qsaObservacao": None,
            "pacoteUsado": 6,
            "saldo": 100.0,
            "consultaID": "0000000000000000000000000000000b",
            "delay": 0.31,
        }

        # cpfcnpj.com.br - package 6 payload of a branch establishment, in the
        # short form (no cnpj_raiz, no filiais).
        cls.mocked_response_cpfcnpj_filial = {
            "status": 1,
            "cnpj": "48412392000203",
            "tipo": "Filial",
            "razao": "Empresa Exemplo Unidade Filial Ltda",
            "fantasia": "Exemplo Filial",
            "capitalSocial": 150000.0,
            "inicioAtividade": "02/09/2020",
            "email": "filial@exemplo.com.br",
            "responsavel": None,
            "responsavelCpf": None,
            "responsavelQualificacao": None,
            "responsavelFederativo": "",
            "simplesNacional": {"optante": "Nao", "inicio": None, "fim": None},
            "matrizEndereco": {
                "cep": "30140071",
                "tipo": "Rua",
                "logradouro": "dos Andradas",
                "numero": "50",
                "complemento": "Loja 2",
                "bairro": "Centro",
                "cidade": "Belo Horizonte",
                "uf": "MG",
            },
            "ibge": {
                "pais": {"id": "1058", "iso2": "BR", "iso3": "BRA", "nome": "Brasil"},
                "estado": {"sigla": "MG"},
                "cidade": {"nome": "Belo Horizonte"},
            },
            "matrizfilial": {"id": 2, "tipo": "Filial"},
            "telefones": [{"ddd": "31", "numero": "40421005"}],
            "fax": {"ddd": None, "numero": None},
            "situacao": {"id": 2, "nome": "Ativa", "data": "02/09/2020", "motivo": []},
            "naturezaJuridica": {
                "codigo": "2062",
                "descricao": "Sociedade Empresaria Limitada",
            },
            "cnae": {
                "fiscal": "9313100",
                "secao": None,
                "divisao": None,
                "grupo": None,
                "classe": None,
                "subClasse": None,
                "descricao": "Atividades de condicionamento fisico",
                "secundarias": [],
            },
            "porte": {"id": "", "descricao": "Micro Empresa"},
            "regimesTributarios": [],
            "comprovantePdfBase64": _PDF_MINIMO_B64,
            "dispensa": {
                "estabelecimento": None,
                "uf_municipio": None,
                "condicoes": [],
            },
            "socios": [
                {
                    "cpf_cnpj_socio": None,
                    "nome": "Maria Socia Exemplo",
                    "tipo": "Pessoa Fisica",
                    "data_entrada": None,
                    "cpf_representante_legal": None,
                    "nome_representante": None,
                    "faixa_etaria": None,
                    "atualizado_em": None,
                    "pais_id": None,
                    "qualificacao_socio": {
                        "id": 49,
                        "descricao": "Socio-Administrador",
                    },
                    "qualificacao_representante": None,
                    "pais": {"nome": "Brasil"},
                }
            ],
            "qsaObservacao": None,
            "pacoteUsado": 6,
            "saldo": 100.0,
            "consultaID": "0000000000000000000000000000000c",
            "delay": 0.28,
        }

        # cpfcnpj.com.br - package 16 payload (state registration): one active
        # (SP) and one inactive (MG).
        cls.mocked_response_cpfcnpj_ie = {
            "status": 1,
            "cnpj": "13347016000117",
            "razao": "Empresa Exemplo Comercio e Servicos Ltda",
            "inscricoesEstaduais": [
                {
                    "inscricao_estadual": "123456789",
                    "ativo": True,
                    "atualizado_em": "2026-09-05T00:00:00.000Z",
                    "estado": {
                        "id": 26,
                        "nome": "Sao Paulo",
                        "sigla": "SP",
                        "ibge_id": 35,
                    },
                },
                {
                    "inscricao_estadual": "0987654321012",
                    "ativo": False,
                    "atualizado_em": "2025-11-02T04:44:52.850Z",
                    "estado": {
                        "id": 11,
                        "nome": "Minas Gerais",
                        "sigla": "MG",
                        "ibge_id": 31,
                    },
                },
            ],
            "pacoteUsado": 16,
            "saldo": 100.0,
            "consultaID": "0000000000000000000000000000000d",
            "delay": 0.30,
        }

        # cpfcnpj.com.br - error payload (HTTP 400) for an invalid CNPJ.
        cls.mocked_response_cpfcnpj_erro = {
            "status": 0,
            "cnpj": "",
            "razao": "",
            "erro": "CNPJ invalido!",
            "pacoteUsado": 6,
            "erroCodigo": 200,
        }

    @classmethod
    def set_param(cls, param_name, param_value):
        (
            cls.env["ir.config_parameter"]
            .sudo()
            .set_param("l10n_br_cnpj_search." + param_name, param_value)
        )
