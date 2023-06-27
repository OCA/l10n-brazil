# Copyright 2022 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import time  # You can't send multiple requests at the same time in trial version
from datetime import datetime
from os import environ
from unittest import mock

from decorator import decorate

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import TestCnpjCommon

_logger = logging.getLogger(__name__)


def _not_every_day_test(method, self, modulo=7, remaining=0):
    if datetime.now().day % modulo == remaining:
        return method(self)
    elif environ.get("CI_FORCE_serpro"):
        return method(self)
    else:
        return lambda: _logger.info(
            "Skipping test today because datetime.now().day %% %s != %s"
            % (modulo, remaining)
        )


def not_every_day_test(method):
    """
    Decorate test methods to query the SERPRO only
    1 day out of 7 and skip tests otherwise in order to prevent
    errors in the API to disrupt the tests from l10n-br test suite.
    The CI_FORCE_serpro env var can be set to force the test anyhow.
    """
    return decorate(method, _not_every_day_test)


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def ok(self):
            return True

        def json(self):
            return self.json_data

    return MockResponse(
        {
            "ni": "34238864000168",
            "tipoEstabelecimento": "1",
            "nomeEmpresarial": "UHIEQKX WHNHIWD NH  FIXKHUUWPHMVX NH NWNXU (UHIFIX)",
            "nomeFantasia": "UHIFIX UHNH",
            "situacaoCadastral": {"codigo": "2", "data": "2019-06-19", "motivo": ""},
            "naturezaJuridica": {"codigo": "2011", "descricao": "Empresa Pública"},
            "dataAbertura": "1967-06-30",
            "cnaePrincipal": {
                "codigo": "6204000",
                "descricao": "Consultoria em tecnologia da informação",
            },
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
            "municipioJurisdicao": {"codigo": "0110100", "descricao": "BRASÍLIA"},
            "telefones": [
                {"ddd": "61", "numero": "22222222"},
                {"ddd": "61", "numero": "33333333"},
            ],
            "correioEletronico": "EMPRESA@EMPRESA.BR",
            "capitalSocial": 0,
            "porte": "05",
            "situacaoEspecial": "",
            "dataSituacaoEspecial": "",
            "informacoesAdicionais": {},
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
        }
    )


@tagged("post_install", "-at_install")
class TestTestSerPro(TestCnpjCommon):
    def setUp(self):
        super(TestTestSerPro, self).setUp()

        self.set_param("cnpj_provider", "serpro")
        self.set_param("serpro_token", "06aef429-a981-3ec5-a1f8-71d38d86481e")
        self.set_param("serpro_trial", True)
        self.set_param("serpro_schema", "basica")

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_mock(self, mock_get):
        self.model.search([("cnpj_cpf", "=", "34.238.864/0001-68")]).unlink()
        self.set_param("serpro_schema", "empresa")

        dummy_empresa = self.model.create(
            {"name": "Dummy Empresa", "cnpj_cpf": "34.238.864/0001-68"}
        )

        time.sleep(3)  # Pause
        dummy_empresa._onchange_cnpj_cpf()
        dummy_empresa.search_cnpj()
        self.assertEqual(dummy_empresa.name, "Uhifix Uhnh")
        self.assertEqual(dummy_empresa.email, "EMPRESA@EMPRESA.BR")
        self.assertEqual(dummy_empresa.street_name, "Nh Biwmnh Wihw Mxivh")
        self.assertEqual(dummy_empresa.street2, "Lote V")
        self.assertEqual(dummy_empresa.street_number, "Q.601")
        self.assertEqual(dummy_empresa.zip, "70836900")
        self.assertEqual(dummy_empresa.district, "Asa Norte")
        self.assertEqual(dummy_empresa.phone, "(61) 22222222")
        self.assertEqual(dummy_empresa.mobile, "(61) 33333333")
        self.assertEqual(dummy_empresa.state_id.code, "DF")
        self.assertEqual(dummy_empresa.equity_capital, 0)
        self.assertEqual(dummy_empresa.cnae_main_id.code, "6204-0/00")

    @not_every_day_test
    def test_serpro_basica(self):
        dummy_basica = self.model.create(
            {"name": "Dummy Basica", "cnpj_cpf": "34.238.864/0001-68"}
        )
        time.sleep(3)
        dummy_basica._onchange_cnpj_cpf()
        dummy_basica.search_cnpj()

        self.assertEqual(dummy_basica.company_type, "company")
        self.assertEqual(
            dummy_basica.legal_name,
            "Uhieqkx Whnhiwd Nh Fixkhuuwphmvx Nh Nwnxu (Uhifix)",
        )
        self.assertEqual(dummy_basica.name, "Uhifix Uhnh")
        self.assertEqual(dummy_basica.email, "EMPRESA@XXXXXX.BR")
        self.assertEqual(dummy_basica.street_name, "Nh Biwmnh Wihw Mxivh")
        self.assertEqual(dummy_basica.street2, "Lote V")
        self.assertEqual(dummy_basica.street_number, "Q.601")
        self.assertEqual(dummy_basica.zip, "70836900")
        self.assertEqual(dummy_basica.district, "Asa Norte")
        self.assertEqual(dummy_basica.phone, "(61) 22222222")
        self.assertEqual(dummy_basica.mobile, "(61) 22222222")
        self.assertEqual(dummy_basica.state_id.code, "DF")
        self.assertEqual(dummy_basica.equity_capital, 0)
        self.assertEqual(dummy_basica.cnae_main_id.code, "6204-0/00")

    @not_every_day_test
    def test_serpro_not_found(self):
        # Na versão Trial só há alguns registros de CNPJ cadastrados
        invalid = self.model.create(
            {"name": "invalid", "cnpj_cpf": "44.356.113/0001-08"}
        )
        invalid._onchange_cnpj_cpf()

        time.sleep(3)  # Pause
        with self.assertRaises(ValidationError):
            invalid.search_cnpj()

    def assert_socios(self, partner, expected_cnpjs):
        socios = self.model.search_read(
            [("id", "in", partner.child_ids.ids)],
            fields=["name", "cnpj_cpf", "company_type"],
        )

        for s in socios:
            s.pop("id")

        expected_socios = [
            {
                "name": "Joana Alves Mundim Pena",
                "cnpj_cpf": expected_cnpjs["Joana"],
                "company_type": "person",
            },
            {
                "name": "Luiza Aldenora",
                "cnpj_cpf": expected_cnpjs["Aldenora"],
                "company_type": "person",
            },
            {
                "name": "Luiza Araujo De Oliveira",
                "cnpj_cpf": expected_cnpjs["Araujo"],
                "company_type": "person",
            },
            {
                "name": "Luiza Barbosa Bezerra",
                "cnpj_cpf": expected_cnpjs["Barbosa"],
                "company_type": "person",
            },
            {
                "name": "Marcelo Antonio Barros De Cicco",
                "cnpj_cpf": expected_cnpjs["Marcelo"],
                "company_type": "person",
            },
        ]

        self.assertEqual(socios, expected_socios)

    @not_every_day_test
    def test_serpro_empresa(self):
        self.model.search([("cnpj_cpf", "=", "34.238.864/0001-68")]).write(
            {"active": False}
        )
        self.set_param("serpro_schema", "empresa")

        dummy_empresa = self.model.create(
            {"name": "Dummy Empresa", "cnpj_cpf": "34.238.864/0001-68"}
        )

        time.sleep(3)  # Pause
        dummy_empresa._onchange_cnpj_cpf()
        dummy_empresa.search_cnpj()

        expected_cnpjs = {
            "Joana": "23982012600",
            "Aldenora": "76822320300",
            "Araujo": "07119488449",
            "Barbosa": "13946994415",
            "Marcelo": "00031298702",
        }

        self.assert_socios(dummy_empresa, expected_cnpjs)

    @not_every_day_test
    def test_serpro_qsa(self):
        self.model.search([("cnpj_cpf", "=", "34.238.864/0001-68")]).write(
            {"active": False}
        )
        self.set_param("serpro_schema", "qsa")

        dummy_qsa = self.model.create(
            {"name": "Dummy QSA", "cnpj_cpf": "34.238.864/0001-68"}
        )

        time.sleep(3)  # Pause
        dummy_qsa._onchange_cnpj_cpf()
        dummy_qsa.search_cnpj()

        expected_cnpjs = {
            "Joana": False,
            "Aldenora": False,
            "Araujo": False,
            "Barbosa": False,
            "Marcelo": False,
        }

        self.assert_socios(dummy_qsa, expected_cnpjs)
