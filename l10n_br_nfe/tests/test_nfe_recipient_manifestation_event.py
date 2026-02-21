# Copyright (C) 2023 - TODAY Felipe Zago - KMEE
# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from unittest import mock

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

response_confirmacao_operacao = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"><retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote /><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>128</cStat><xMotivo>Lote de Evento Processado</xMotivo><retEvento versao="1.00"><infEvento><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>135</cStat><xMotivo>Evento registrado e vinculado a NF-e</xMotivo><chNFe>31201010588201000105550010038421171838422178</chNFe><tpEvento>210200</tpEvento><xEvento>Confirmacao da Operacao</xEvento><nSeqEvento>1</nSeqEvento><CNPJDest>81583054000129</CNPJDest><dhRegEvento>2023-07-10T10:00:00-03:00</dhRegEvento><nProt>12345</nProt></infEvento></retEvento></retEnvEvento></nfeResultMsg></soap:Body></soap:Envelope>"""  # noqa: E501
response_confirmacao_operacao_rejeicao = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"><retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote /><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>128</cStat><xMotivo>Lote de Evento Processado</xMotivo><retEvento versao="1.00"><infEvento><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>573</cStat><xMotivo>Rejeicao: Duplicidade de Evento</xMotivo><chNFe>31201010588201000105550010038421171838422178</chNFe><tpEvento>210200</tpEvento><nSeqEvento>1</nSeqEvento><CNPJDest>81583054000129</CNPJDest><dhRegEvento>2023-07-10T10:00:00-03:00</dhRegEvento><nProt>54321</nProt></infEvento></retEvento></retEnvEvento></nfeResultMsg></soap:Body></soap:Envelope>"""  # noqa: E501
response_ciencia_operacao = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"><retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote>123</idLote><tpAmb>2</tpAmb><verAplic>app-ver</verAplic><cOrgao>91</cOrgao><cStat>128</cStat><xMotivo>Lote de Evento Processado</xMotivo><retEvento versao="1.00"><infEvento Id="ID1210210..."><tpAmb>2</tpAmb><verAplic>app-ver</verAplic><cOrgao>91</cOrgao><cStat>135</cStat><xMotivo>Evento registrado e vinculado a NF-e</xMotivo><chNFe>31201010588201000105550010038421171838422178</chNFe><tpEvento>210210</tpEvento><xEvento>Ciencia da Operacao</xEvento><nSeqEvento>1</nSeqEvento><CNPJDest>81583054000129</CNPJDest><dhRegEvento>2023-07-10T10:00:00-03:00</dhRegEvento><nProt>12345</nProt></infEvento></retEvento></retEnvEvento></nfeResultMsg></soap:Body></soap:Envelope>"""  # noqa: E501
response_desconhecimento_operacao = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"><retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote>123</idLote><tpAmb>2</tpAmb><verAplic>app-ver</verAplic><cOrgao>91</cOrgao><cStat>128</cStat><xMotivo>Lote de Evento Processado</xMotivo><retEvento versao="1.00"><infEvento Id="ID1210220..."><tpAmb>2</tpAmb><verAplic>app-ver</verAplic><cOrgao>91</cOrgao><cStat>135</cStat><xMotivo>Evento registrado e vinculado a NF-e</xMotivo><chNFe>31201010588201000105550010038421171838422178</chNFe><tpEvento>210220</tpEvento><xEvento>Desconhecimento da Operacao</xEvento><nSeqEvento>1</nSeqEvento><CNPJDest>81583054000129</CNPJDest><dhRegEvento>2023-07-10T10:00:00-03:00</dhRegEvento><nProt>12345</nProt></infEvento></retEvento></retEnvEvento></nfeResultMsg></soap:Body></soap:Envelope>"""  # noqa: E501
response_operacao_nao_realizada = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"><retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote>123</idLote><tpAmb>2</tpAmb><verAplic>app-ver</verAplic><cOrgao>91</cOrgao><cStat>128</cStat><xMotivo>Lote de Evento Processado</xMotivo><retEvento versao="1.00"><infEvento Id="ID1210240..."><tpAmb>2</tpAmb><verAplic>app-ver</verAplic><cOrgao>91</cOrgao><cStat>135</cStat><xMotivo>Evento registrado e vinculado a NF-e</xMotivo><chNFe>31201010588201000105550010038421171838422178</chNFe><tpEvento>210240</tpEvento><xEvento>Operacao nao Realizada</xEvento><nSeqEvento>1</nSeqEvento><CNPJDest>81583054000129</CNPJDest><dhRegEvento>2023-07-10T10:00:00-03:00</dhRegEvento><nProt>12345</nProt></infEvento></retEvento></retEnvEvento></nfeResultMsg></soap:Body></soap:Envelope>"""  # noqa: E501


class _InfEvento:
    def __init__(self, cStat="135", xMotivo="Evento registrado e vinculado a NF-e"):
        self.cStat = cStat
        self.xMotivo = xMotivo
        self.nProt = "12345"
        self.dhRegEvento = "2023-07-10T10:00:00-03:00"


class _RetEvento:
    def __init__(self, infEvento):
        self.infEvento = infEvento


class _Resposta:
    def __init__(self, inf_cstat="135", inf_xmotivo="OK"):
        self.cStat = "128"
        self.xMotivo = "Lote de Evento Processado"
        self.retEvento = [_RetEvento(_InfEvento(cStat=inf_cstat, xMotivo=inf_xmotivo))]


class _Retorno:
    def __init__(self, status_code=200):
        self.status_code = status_code
        self._content = b"<xml>fake</xml>"


class _FakeResult:
    def __init__(self, status_code=200, inf_cstat="135", inf_xmotivo="OK"):
        self.retorno = _Retorno(status_code=status_code)
        self.resposta = _Resposta(inf_cstat=inf_cstat, inf_xmotivo=inf_xmotivo)


class _FakeProcessor:
    """Emulates the MDeAdapter returning _FakeResult for each operation."""

    def __init__(self, mapa=None):
        self._mapa = mapa or {}

    def _get(self, name):
        return self._mapa.get(name, _FakeResult())

    def ciencia_da_operacao(self, chave, cnpj_dest):
        return self._get("ciencia_da_operacao")

    def confirmacao_da_operacao(self, chave, cnpj_dest):
        return self._get("confirmacao_da_operacao")

    def desconhecimento_da_operacao(self, chave, cnpj_dest):
        return self._get("desconhecimento_da_operacao")

    def operacao_nao_realizada(self, chave, cnpj_dest):
        return self._get("operacao_nao_realizada")


class TestNFeMDE(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_simples_nacional")
        cls.mde_id = cls.env["l10n_br_nfe.md_event"].create(
            {
                "company_id": cls.company.id,
                "access_key": "31201010588201000105550010038421171838422178",
                "document_number": 3842117,
                "event_type": "ciente",
                "state": "draft",
            }
        )

    def test_events_success(self):
        proc = _FakeProcessor(
            {
                "confirmacao_da_operacao": _FakeResult(inf_cstat="135"),
                "ciencia_da_operacao": _FakeResult(inf_cstat="135"),
                "desconhecimento_da_operacao": _FakeResult(inf_cstat="135"),
                "operacao_nao_realizada": _FakeResult(inf_cstat="135"),
            }
        )

        with mock.patch(
            "odoo.addons.l10n_br_nfe.models.nfe_md_event.NfeRecipientManifestationEvent._get_processor",
            return_value=proc,
        ):
            self.mde_id.event_type = "confirmado"
            self.mde_id.action_confirm()
            self.assertEqual(self.mde_id.event_type, "confirmado")

            self.mde_id.event_type = "ciente"
            self.mde_id.action_confirm()
            self.assertEqual(self.mde_id.event_type, "ciente")
            self.assertEqual(
                self.mde_id.display_name,
                "31201010588201000105550010038421171838422178",
            )

            self.mde_id.event_type = "desconhecido"
            self.mde_id.action_confirm()
            self.assertEqual(self.mde_id.event_type, "desconhecido")

            self.mde_id.event_type = "nao_realizado"
            self.mde_id.action_confirm()
            self.assertEqual(self.mde_id.event_type, "nao_realizado")

    def test_event_error(self):
        proc_http = _FakeProcessor(
            {"confirmacao_da_operacao": _FakeResult(status_code=500)}
        )
        with (
            mock.patch(
                "odoo.addons.l10n_br_nfe.models.nfe_md_event.NfeRecipientManifestationEvent._get_processor",
                return_value=proc_http,
            ),
            self.assertRaises(ValidationError),
        ):
            self.mde_id.event_type = "confirmado"
            self.mde_id.action_confirm()

    def test_event_573_duplicate_treated_as_done(self):
        """Error 573 (duplicate event) should mark MDE as done, not raise."""
        proc_573 = _FakeProcessor(
            {
                "confirmacao_da_operacao": _FakeResult(
                    inf_cstat="573", inf_xmotivo="Rejeicao: Duplicidade de Evento"
                )
            }
        )
        with mock.patch(
            "odoo.addons.l10n_br_nfe.models.nfe_md_event.NfeRecipientManifestationEvent._get_processor",
            return_value=proc_573,
        ):
            self.mde_id.event_type = "confirmado"
            self.mde_id.state = "draft"
            self.mde_id.action_confirm()

        self.assertEqual(self.mde_id.state, "done")
        self.assertTrue(self.mde_id.response_xml)
