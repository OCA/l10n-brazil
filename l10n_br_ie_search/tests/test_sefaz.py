# Copyright 2023 KMEE
# Copyright (C) 2024-Today - Engenere (<https://engenere.one>).
# @author Cristiano Mafra Junior
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import os
from datetime import timedelta
from unittest.mock import patch

import vcr
from erpbrasil.assinatura import misc

from odoo import fields
from odoo.tests import Form, tagged
from odoo.tests.common import SavepointCase
from odoo.tools.misc import format_date


class FakeRetorno:
    __slots__ = "text", "ok"


@tagged("post_install", "-at_install")
class TestSefaz(SavepointCase):
    def setUp(self):
        super().setUp()
        self.retorno = FakeRetorno()
        self.retorno.text = """<?xml version="1.0" encoding="utf-8"?><soap:Envelope
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
        self.retorno.ok = (True,)
        self.set_param("ie_search", "sefaz")
        self.model = self.env["res.company"]
        self.company_model = self.env["res.company"]
        self.certificate_model = self.env["l10n_br_fiscal.certificate"]
        self.cert_passwd = "123456"
        self.cert_country = "BR"
        self.cert_issuer_a = "EMISSOR A TESTE"
        self.cert_issuer_b = "EMISSOR B TESTE"
        self.cert_subject_valid = "CERTIFICADO VALIDO TESTE"
        self.cert_date_exp = fields.Datetime.today() + timedelta(days=365)
        self.cert_subject_invalid = "CERTIFICADO INVALIDO TESTE"
        self.cert_name = "{} - {} - {} - Valid: {}".format(
            "NF-E",
            "A1",
            self.cert_subject_valid,
            format_date(self.env, self.cert_date_exp),
        )

        self.certificate_valid = misc.create_fake_certificate_file(
            valid=True,
            passwd=self.cert_passwd,
            issuer=self.cert_issuer_a,
            country=self.cert_country,
            subject=self.cert_subject_valid,
        )
        self.certificate_invalid = misc.create_fake_certificate_file(
            valid=False,
            passwd=self.cert_passwd,
            issuer=self.cert_issuer_b,
            country=self.cert_country,
            subject=self.cert_subject_invalid,
        )
        self.cert = self.certificate_model.create(
            {
                "type": "nf-e",
                "subtype": "a1",
                "password": self.cert_passwd,
                "file": self.certificate_valid,
            }
        )

    def set_param(self, param_name, param_value):
        (
            self.env["ir.config_parameter"]
            .sudo()
            .set_param("l10n_br_ie_search." + param_name, param_value)
        )

    def _switch_user_company(self, user, company):
        """Add a company to the user's allowed & set to current."""
        user.write(
            {
                "company_ids": [(6, 0, (company + user.company_ids).ids)],
                "company_id": company.id,
            }
        )

    @vcr.use_cassette(
        os.path.dirname(__file__) + "/fixtures/test_sefaz.yaml",
        match_on=["method", "scheme", "host", "port", "path", "query", "body"],
        ignore_localhost=True,
    )
    def test_sefaz(self):
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
            wizard = Form(
                self.env["partner.search.wizard"]
                .with_context(wizard_context)
                .create({})
            ).save()
            wizard.action_update_partner()
            self.assertEqual(dummy.inscr_est, "528388258640")
