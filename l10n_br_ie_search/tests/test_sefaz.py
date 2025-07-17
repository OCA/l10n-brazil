# Copyright 2023 KMEE
# Copyright (C) 2024-Today - Engenere (<https://engenere.one>).
# @author Cristiano Mafra Junior
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import timedelta
from unittest import mock
from unittest.mock import patch

from erpbrasil.assinatura import misc

from odoo import Command, fields
from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase
from odoo.tools.misc import format_date


class FakeRetorno:
    __slots__ = "text", "ok"


@tagged("post_install", "-at_install")
class TestSefaz(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.retorno = FakeRetorno()
        cls.retorno.text = """<?xml version="1.0" encoding="utf-8"?><soap:Envelope
            xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xmlns:xsd="http://www.w3.org/2001/XMLSchema"><soap:Body>
            <nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/CadConsultaCadastro4">
            <retConsCad versao="2.00" xmlns="http://www.portalfiscal.inf.br/nfe">
            <infCons><verAplic>SP_NFE_PL009_V4</verAplic><cStat>111</cStat>
            <xMotivo>Consulta cadastro com uma ocorrência</xMotivo><UF>SP</UF>
            <CNPJ>88.570.377/0001-27</CNPJ>
            <dhCons>2023-07-06T10:11:50-03:00</dhCons><cUF>35</cUF><infCad>
            <IE>528388258640</IE>
            <CNPJ>88.570.377/0001-27</CNPJ><UF>SP</UF><cSit>1</cSit>
            <indCredNFe>1</indCredNFe>
            <indCredCTe>4</indCredCTe><xNome>Dummy Empresa</xNome>
            <xRegApur>NORMAL - REGIME PERIÓDICO DE APURAÇÃO</xRegApur>
            <CNAE>9430800</CNAE><dIniAtiv>2017-10-16</dIniAtiv>
            <dUltSit>2017-10-16</dUltSit><ender><xLgr>RUA DUMMY</xLgr>
            <nro>250</nro>
            <xBairro>VILA FELIZ</xBairro><cMun>3550308</cMun>
            <xMun>SAO PAULO</xMun>
            <CEP>01222001</CEP>
            </ender></infCad></infCons></retConsCad></nfeResultMsg>
            </soap:Body></soap:Envelope>"""
        cls.retorno.ok = (True,)
        cls.set_param("ie_search", "sefaz")
        cls.model = cls.env["res.company"]
        cls.company_model = cls.env["res.company"]
        cls.certificate_model = cls.env["l10n_br_fiscal.certificate"]
        cls.cert_passwd = "123456"
        cls.cert_country = "BR"
        cls.cert_issuer_a = "EMISSOR A TESTE"
        cls.cert_issuer_b = "EMISSOR B TESTE"
        cls.cert_subject_valid = "CERTIFICADO VALIDO TESTE"
        cls.cert_date_exp = fields.Datetime.today() + timedelta(days=365)
        cls.cert_subject_invalid = "CERTIFICADO INVALIDO TESTE"
        cls.cert_name = "{} - {} - {} - Valid: {}".format(
            "NF-E",
            "A1",
            cls.cert_subject_valid,
            format_date(cls.env, cls.cert_date_exp),
        )

        cls.certificate_valid = misc.create_fake_certificate_file(
            valid=True,
            passwd=cls.cert_passwd,
            issuer=cls.cert_issuer_a,
            country=cls.cert_country,
            subject=cls.cert_subject_valid,
        )
        cls.certificate_invalid = misc.create_fake_certificate_file(
            valid=False,
            passwd=cls.cert_passwd,
            issuer=cls.cert_issuer_b,
            country=cls.cert_country,
            subject=cls.cert_subject_invalid,
        )
        cls.cert = cls.certificate_model.create(
            {
                "type": "nf-e",
                "subtype": "a1",
                "password": cls.cert_passwd,
                "file": cls.certificate_valid,
            }
        )

    @classmethod
    def set_param(cls, param_name, param_value):
        (
            cls.env["ir.config_parameter"]
            .sudo()
            .set_param("l10n_br_ie_search." + param_name, param_value)
        )

    def _switch_user_company(self, user, company):
        """Add a company to the user's allowed & set to current."""
        user.write(
            {
                "company_ids": [Command.set((company + user.company_ids).ids)],
                "company_id": company.id,
            }
        )

    def test_sefaz(self):
        mock_response = {
            "abertura": "24/11/2021",
            "situacao": "BAIXADA",
            "tipo": "MATRIZ",
            "nome": "Dummy Empresa",
            "porte": "MICRO EMPRESA",
            "natureza_juridica": "213-5 - Empresário (Individual)",
            "logradouro": "RUA DUMMY",
            "numero": "250",
            "complemento": "BLOCO E;APT 302",
            "municipio": "SAO PAULO",
            "bairro": "VILA FELIZ",
            "uf": "SP",
            "cep": "01222001",
            "email": "kilian.melcher@gmail.com",
            "telefone": "(83) 8665-0905",
            "data_situacao": "18/12/2023",
            "motivo_situacao": "EXTINÇÃO POR ENCERRAMENTO LIQUIDAÇÃO VOLUNTÁRIA",
            "cnpj": "88570377000127",
            "ultima_atualizacao": "2024-01-13T23:59:59.000Z",
            "status": "OK",
            "fantasia": "",
            "efr": "",
            "situacao_especial": "",
            "data_situacao_especial": "",
            "atividade_principal": [{"code": "4751-2/01", "text": "********"}],
            "atividades_secundarias": [{"code": "00.00-0-00", "text": "Não informada"}],
            "capital_social": "3000.00",
            "qsa": [],
            "extra": {},
            "billing": {"free": True, "database": True},
        }
        with mock.patch(
            "odoo.addons.l10n_br_cnpj_search.models.cnpj_webservice.CNPJWebservice.validate",
            return_value=mock_response,
        ):
            with patch(
                "odoo.addons.l10n_br_ie_search.models.sefaz_webservice.SefazWebservice.sefaz_search"
            ) as mock_get_partner_ie:
                mock_get_partner_ie.return_value = self.retorno
                dummy = self.model.create(
                    {
                        "name": "Dummy",
                        "cnpj_cpf": "88.570.377/0001-27",
                        "certificate_ecnpj_id": self.cert.id,
                    }
                )
                dummy._onchange_cnpj_cpf()
                action_wizard = dummy.action_open_cnpj_search_wizard()
                wizard_context = action_wizard.get("context")
                wizard_context["active_model"] = "res.partner"
                wizard = Form(
                    self.env["partner.search.wizard"]
                    .with_context(**wizard_context)
                    .create({})
                ).save()
                wizard.action_update_partner()
            self.assertEqual(dummy.l10n_br_ie_code, "528388258640")
