# Copyright (C) 2023 - TODAY Felipe Zago - KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from unittest import mock

from xsdata.formats.dataclass.transports import DefaultTransport

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_br_fiscal_dfe.tests.test_dfe import response_sucesso_multiplos

response_confirmacao_operacao = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"><retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote /><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>128</cStat><xMotivo>Lote de Evento Processado</xMotivo><retEvento versao="1.00"><infEvento><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>135</cStat><xMotivo>Evento registrado e vinculado a NF-e</xMotivo><chNFe>31201010588201000105550010038421171838422178</chNFe><tpEvento>210200</tpEvento><xEvento>Confirmacao da Operacao</xEvento><nSeqEvento>1</nSeqEvento><CNPJDest>81583054000129</CNPJDest><dhRegEvento>2023-07-10T10:00:00-03:00</dhRegEvento><nProt>12345</nProt></infEvento></retEvento></retEnvEvento></nfeResultMsg></soap:Body></soap:Envelope>"""  # noqa: E501
response_confirmacao_operacao_rejeicao = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"><retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote /><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>128</cStat><xMotivo>Lote de Evento Processado</xMotivo><retEvento versao="1.00"><infEvento><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>573</cStat><xMotivo>Rejeicao: Duplicidade de Evento</xMotivo><chNFe>31201010588201000105550010038421171838422178</chNFe><tpEvento>210200</tpEvento><nSeqEvento>1</nSeqEvento><CNPJDest>81583054000129</CNPJDest><dhRegEvento>2023-07-10T10:00:00-03:00</dhRegEvento><nProt>54321</nProt></infEvento></retEvento></retEnvEvento></nfeResultMsg></soap:Body></soap:Envelope>"""  # noqa: E501
response_ciencia_operacao = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"><retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote>123</idLote><tpAmb>2</tpAmb><verAplic>app-ver</verAplic><cOrgao>91</cOrgao><cStat>128</cStat><xMotivo>Lote de Evento Processado</xMotivo><retEvento versao="1.00"><infEvento Id="ID1210210..."><tpAmb>2</tpAmb><verAplic>app-ver</verAplic><cOrgao>91</cOrgao><cStat>135</cStat><xMotivo>Evento registrado e vinculado a NF-e</xMotivo><chNFe>31201010588201000105550010038421171838422178</chNFe><tpEvento>210210</tpEvento><xEvento>Ciencia da Operacao</xEvento><nSeqEvento>1</nSeqEvento><CNPJDest>81583054000129</CNPJDest><dhRegEvento>2023-07-10T10:00:00-03:00</dhRegEvento><nProt>12345</nProt></infEvento></retEvento></retEnvEvento></nfeResultMsg></soap:Body></soap:Envelope>"""  # noqa: E501
response_desconhecimento_operacao = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"><retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote>123</idLote><tpAmb>2</tpAmb><verAplic>app-ver</verAplic><cOrgao>91</cOrgao><cStat>128</cStat><xMotivo>Lote de Evento Processado</xMotivo><retEvento versao="1.00"><infEvento Id="ID1210220..."><tpAmb>2</tpAmb><verAplic>app-ver</verAplic><cOrgao>91</cOrgao><cStat>135</cStat><xMotivo>Evento registrado e vinculado a NF-e</xMotivo><chNFe>31201010588201000105550010038421171838422178</chNFe><tpEvento>210220</tpEvento><xEvento>Desconhecimento da Operacao</xEvento><nSeqEvento>1</nSeqEvento><CNPJDest>81583054000129</CNPJDest><dhRegEvento>2023-07-10T10:00:00-03:00</dhRegEvento><nProt>12345</nProt></infEvento></retEvento></retEnvEvento></nfeResultMsg></soap:Body></soap:Envelope>"""  # noqa: E501
response_operacao_nao_realizada = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"><retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote>123</idLote><tpAmb>2</tpAmb><verAplic>app-ver</verAplic><cOrgao>91</cOrgao><cStat>128</cStat><xMotivo>Lote de Evento Processado</xMotivo><retEvento versao="1.00"><infEvento Id="ID1210240..."><tpAmb>2</tpAmb><verAplic>app-ver</verAplic><cOrgao>91</cOrgao><cStat>135</cStat><xMotivo>Evento registrado e vinculado a NF-e</xMotivo><chNFe>31201010588201000105550010038421171838422178</chNFe><tpEvento>210240</tpEvento><xEvento>Operacao nao Realizada</xEvento><nSeqEvento>1</nSeqEvento><CNPJDest>81583054000129</CNPJDest><dhRegEvento>2023-07-10T10:00:00-03:00</dhRegEvento><nProt>12345</nProt></infEvento></retEvento></retEnvEvento></nfeResultMsg></soap:Body></soap:Envelope>"""  # noqa: E501


class _InfEvento:
    def __init__(self, cStat="135", xMotivo="Evento registrado e vinculado a NF-e"):
        self.cStat = cStat
        self.xMotivo = xMotivo


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


class _FakeResult:
    def __init__(self, status_code=200, inf_cstat="135", inf_xmotivo="OK"):
        self.retorno = _Retorno(status_code=status_code)
        self.resposta = _Resposta(inf_cstat=inf_cstat, inf_xmotivo=inf_xmotivo)


class _FakeProcessor:
    """Emula o MDeAdapter retornando _FakeResult para cada operação."""

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
        cls.dfe_monitor = cls.env["l10n_br_fiscal.dfe_monitor"].create(
            {
                "last_nsu": "000000000000001",
                "company_id": cls.env.ref("l10n_br_base.empresa_simples_nacional").id,
            }
        )
        with mock.patch.object(
            DefaultTransport,
            "post",
            return_value=response_sucesso_multiplos.encode("utf-8"),
        ):
            cls.dfe_monitor.search_documents()
            cls.dfe = cls.dfe_monitor.dfe_ids[0]
        cls.mde_id = cls.env["l10n_br_nfe.recipient_manifestation_event"].create(
            {
                "company_id": cls.dfe.company_id.id,
                "key": cls.dfe.key,
                "document_number": cls.dfe.document_number,
                "event_type": "ciente",
                "status": "rascunho",
                "nfe_dfe_bundle_id": cls.dfe.nfe_dfe_bundle_id.id,
                "mde_document_type": "mde_nfe",
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
            "odoo.addons.l10n_br_nfe.models.nfe_recipient_manifestation_event.NfeRecipientManifestationEvent._get_processor",
            return_value=proc,
        ):
            self.mde_id.event_type = "confirmado"
            self.mde_id.action_confirm()
            self.assertEqual(self.mde_id.event_type, "confirmado")

            self.mde_id.event_type = "ciente"
            self.mde_id.action_confirm()
            self.assertEqual(self.mde_id.event_type, "ciente")
            self.assertEqual(
                self.mde_id.display_name, "31201010588201000105550010038421171838422178"
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
                "odoo.addons.l10n_br_nfe.models.nfe_recipient_manifestation_event.NfeRecipientManifestationEvent._get_processor",
                return_value=proc_http,
            ),
            self.assertRaises(ValidationError),
        ):
            self.mde_id.event_type = "confirmado"
            self.mde_id.action_confirm()

        proc_negocio = _FakeProcessor(
            {
                "confirmacao_da_operacao": _FakeResult(
                    inf_cstat="573", inf_xmotivo="Rejeicao: Duplicidade de Evento"
                )
            }
        )
        with (
            mock.patch(
                "odoo.addons.l10n_br_nfe.models.nfe_recipient_manifestation_event.NfeRecipientManifestationEvent._get_processor",
                return_value=proc_negocio,
            ),
            self.assertRaises(ValidationError),
        ):
            self.mde_id.event_type = "confirmado"
            self.mde_id.action_confirm()

    # @mock.patch.object(MDe, "action_ciencia_emissao", return_value=None)
    # def test_download_documents(self, mock_ciencia):
    #     """Test downloading XMLs for one or more MDE records."""
    #     mde_ids = self.mde + self.mde.copy()

    #     # The download action itself triggers a new DFe search to get the full XML.
    #     # We mock this call to return the full document.
    #     with mock.patch.object(
    #         DefaultTransport,
    #         "post",
    #         return_value=response_sucesso_multiplos.encode("utf-8"),
    #     ):
    #         result_single = self.mde.action_download_xml()
    #         result_multiple = mde_ids.action_download_xml()

    #     attachment_single = self.get_attachment_from_result(result_single)
    #     attachment_multiple = self.get_attachment_from_result(result_multiple)

    #     self.assertTrue(attachment_single)
    #     self.assertEqual(attachment_single, self.mde.attachment_id)
    #     self.assertTrue(attachment_multiple)
    #     self.assertEqual(attachment_multiple.name, "attachments.tar.gz")

    # def get_attachment_from_result(self, result):
    #     """Helper to extract the attachment record from the download action result."""
    #     # The URL is in the format /web/content/{attachment_id}/{filename}
    #     url_parts = result["url"].split("/")
    #     # e.g., ['', 'web', 'content', '591', 'filename.xml?download=true']
    #     self.assertGreaterEqual(len(url_parts), 4, "URL format seems incorrect.")
    #     self.assertEqual(url_parts[1], "web")
    #     self.assertEqual(url_parts[2], "content")

    #     attachment_id = int(url_parts[3])
    #     return self.env["ir.attachment"].browse(attachment_id)
