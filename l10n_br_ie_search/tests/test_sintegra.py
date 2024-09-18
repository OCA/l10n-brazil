# Copyright 2023 KMEE
# Copyright (C) 2024-Today - Engenere (<https://engenere.one>).
# @author Cristiano Mafra Junior
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from unittest.mock import patch

from odoo.tests import Form, tagged
from odoo.tests.common import SavepointCase

_logger = logging.getLogger(__name__)


class FakeRetorno:
    __slots__ = "text", "status_code"

    def json(self):
        return self.text


@tagged("post_install", "-at_install")
class TestSintegra(SavepointCase):
    def setUp(self):
        super().setUp()
        self.retorno = FakeRetorno()
        self.retorno.text = {
            "code": "0",
            "status": "OK",
            "message": "Pesquisa realizada com sucesso.",
            "nome_empresarial": "Google brasil internet ltda.",
            "cnpj": "06990590000123",
            "inscricao_estadual": "149848403115",
            "tipo_inscricao": "",
            "data_situacao_cadastral": "16-10-2007",
            "situacao_cnpj": "Sem restrição",
            "situacao_ie": "Ativo",
            "nome_fantasia": "",
            "data_inicio_atividade": "16-10-2007",
            "regime_tributacao": "Normal - regime periódico de apuração",
            "informacao_ie_como_destinatario": "Não informado",
            "porte_empresa": "Não informado",
            "cnae_principal": {
                "code": "6319400",
                "text": "Portais, provedores"
                + " de conteúdo e outros serviços de informação na internet",
            },
            "data_fim_atividade": "",
            "uf": "SP",
            "municipio": "São Paulo",
            "logradouro": "Avenida brigadeiro faria lima",
            "complemento": "Andar 17 a 20 torre sul andar"
            + "2 torre norte andar 18 a 20 torre norte",
            "cep": "04538133",
            "numero": "3477",
            "bairro": "Itaim bibi",
            "ibge": {"codigo_municipio": "3550308", "codigo_uf": "35"},
        }
        self.retorno.status_code = 200
        self.model = self.env["res.partner"]
        self.set_param_cnpj("cnpj_provider", "receitaws")
        self.set_param("sintegra_token", "C3144731-15F5-4F87-AC74-8887E4900A13")
        self.set_param("ie_search", "sintegraws")

    def set_param_cnpj(self, param_name, param_value):
        (
            self.env["ir.config_parameter"]
            .sudo()
            .set_param("l10n_br_cnpj_search." + param_name, param_value)
        )

    def set_param(self, param_name, param_value):
        (
            self.env["ir.config_parameter"]
            .sudo()
            .set_param("l10n_br_ie_search." + param_name, param_value)
        )

    @patch("requests.get")
    def test_sintegra(self, mock_get_partner_ie):
        mock_get_partner_ie.return_value = self.retorno
        dummy = self.model.create({"name": "Dummy", "cnpj_cpf": "06990590000123"})
        dummy._onchange_cnpj_cpf()
        action_wizard = dummy.action_open_cnpj_search_wizard()
        wizard_context = action_wizard.get("context")
        wizard = Form(
            self.env["partner.search.wizard"].with_context(wizard_context).create({})
        ).save()
        wizard.action_update_partner()
        self.assertEqual(dummy.inscr_est, "149848403115")
