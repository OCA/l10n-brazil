# Copyright (C) 2023 - TODAY Felipe Zago - KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from unittest import mock
from erpbrasil.nfelib_legacy.v4_00 import retEnvEvento
from requests.exceptions import RequestException

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_br_fiscal_dfe.tests.test_dfe import response_sucesso_multiplos

from ..models.mde import MDe

response_confirmacao_operacao = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"><retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote /><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>128</cStat><xMotivo>Lote de Evento Processado</xMotivo><retEvento versao="1.00"><infEvento><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>135</cStat><xMotivo>Evento registrado e vinculado a NF-e</xMotivo><chNFe>31201010588201000105550010038421171838422178</chNFe><tpEvento>210200</tpEvento><xEvento>Confirmacao da Operacao</xEvento><nSeqEvento>1</nSeqEvento><CNPJDest>81583054000129</CNPJDest><dhRegEvento>2023-07-10T10:00:00-03:00</dhRegEvento><nProt>12345</nProt></infEvento></retEvento></retEnvEvento></nfeResultMsg></soap:Body></soap:Envelope>"""  # noqa: E501
response_confirmacao_operacao_rejeicao = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"><retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote /><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>128</cStat><xMotivo>Lote de Evento Processado</xMotivo><retEvento versao="1.00"><infEvento><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>573</cStat><xMotivo>Rejeicao: Duplicidade de Evento</xMotivo><chNFe>31201010588201000105550010038421171838422178</chNFe><tpEvento>210200</tpEvento><nSeqEvento>1</nSeqEvento><CNPJDest>81583054000129</CNPJDest><dhRegEvento>2023-07-10T10:00:00-03:00</dhRegEvento><nProt>54321</nProt></infEvento></retEvento></retEnvEvento></nfeResultMsg></soap:Body></soap:Envelope>"""  # noqa: E501
response_ciencia_operacao = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"><retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote>123</idLote><tpAmb>2</tpAmb><verAplic>app-ver</verAplic><cOrgao>91</cOrgao><cStat>128</cStat><xMotivo>Lote de Evento Processado</xMotivo><retEvento versao="1.00"><infEvento Id="ID1210210..."><tpAmb>2</tpAmb><verAplic>app-ver</verAplic><cOrgao>91</cOrgao><cStat>135</cStat><xMotivo>Evento registrado e vinculado a NF-e</xMotivo><chNFe>31201010588201000105550010038421171838422178</chNFe><tpEvento>210210</tpEvento><xEvento>Ciencia da Operacao</xEvento><nSeqEvento>1</nSeqEvento><CNPJDest>81583054000129</CNPJDest><dhRegEvento>2023-07-10T10:00:00-03:00</dhRegEvento><nProt>12345</nProt></infEvento></retEvento></retEnvEvento></nfeResultMsg></soap:Body></soap:Envelope>"""  # noqa: E501
response_desconhecimento_operacao = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"><retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote>123</idLote><tpAmb>2</tpAmb><verAplic>app-ver</verAplic><cOrgao>91</cOrgao><cStat>128</cStat><xMotivo>Lote de Evento Processado</xMotivo><retEvento versao="1.00"><infEvento Id="ID1210220..."><tpAmb>2</tpAmb><verAplic>app-ver</verAplic><cOrgao>91</cOrgao><cStat>135</cStat><xMotivo>Evento registrado e vinculado a NF-e</xMotivo><chNFe>31201010588201000105550010038421171838422178</chNFe><tpEvento>210220</tpEvento><xEvento>Desconhecimento da Operacao</xEvento><nSeqEvento>1</nSeqEvento><CNPJDest>81583054000129</CNPJDest><dhRegEvento>2023-07-10T10:00:00-03:00</dhRegEvento><nProt>12345</nProt></infEvento></retEvento></retEnvEvento></nfeResultMsg></soap:Body></soap:Envelope>"""  # noqa: E501
response_operacao_nao_realizada = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"><retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote>123</idLote><tpAmb>2</tpAmb><verAplic>app-ver</verAplic><cOrgao>91</cOrgao><cStat>128</cStat><xMotivo>Lote de Evento Processado</xMotivo><retEvento versao="1.00"><infEvento Id="ID1210240..."><tpAmb>2</tpAmb><verAplic>app-ver</verAplic><cOrgao>91</cOrgao><cStat>135</cStat><xMotivo>Evento registrado e vinculado a NF-e</xMotivo><chNFe>31201010588201000105550010038421171838422178</chNFe><tpEvento>210240</tpEvento><xEvento>Operacao nao Realizada</xEvento><nSeqEvento>1</nSeqEvento><CNPJDest>81583054000129</CNPJDest><dhRegEvento>2023-07-10T10:00:00-03:00</dhRegEvento><nProt>12345</nProt></infEvento></retEvento></retEnvEvento></nfeResultMsg></soap:Body></soap:Envelope>"""  # noqa: E501


class TestNFeMDE(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")

        cls.dfe = cls.env["l10n_br_fiscal.dfe"].create({"company_id": cls.company.id})

        # Mock the initial DFe search to populate the MDE records for testing
        with mock.patch.object(
            DefaultTransport,
            "post",
            return_value=response_sucesso_multiplos.encode("utf-8"),
        ):
            cls.dfe.search_documents()

        # We test the first MDE, which is a resNFe from the fixture
        cls.mde = cls.dfe.mde_ids[0]

    def test_events_success(self):
        """Test the successful execution of all manifestation events."""
        with mock.patch.object(
            DefaultTransport,
            "post",
            return_value=response_confirmacao_operacao.encode("utf-8"),
        ) as mock_post:
            self.mde.action_confirmar_operacacao()
            self.assertEqual(self.mde.state, "confirmado")
            mock_post.assert_called_once()

        with mock.patch.object(
            DefaultTransport,
            "post",
            return_value=response_ciencia_operacao.encode("utf-8"),
        ) as mock_post:
            self.mde.action_ciencia_emissao()
            self.assertEqual(self.mde.state, "ciente")
            mock_post.assert_called_once()

        with mock.patch.object(
            DefaultTransport,
            "post",
            return_value=response_desconhecimento_operacao.encode("utf-8"),
        ) as mock_post:
            self.mde.action_operacao_desconhecida()
            self.assertEqual(self.mde.state, "desconhecido")
            mock_post.assert_called_once()

        with mock.patch.object(
            DefaultTransport,
            "post",
            return_value=response_operacao_nao_realizada.encode("utf-8"),
        ) as mock_post:
            self.mde.action_negar_operacao()
            self.assertEqual(self.mde.state, "nao_realizado")
            mock_post.assert_called_once()

    def test_event_error(self):
        """Test error handling for manifestation events."""
        # Test case for a network/HTTP error
        with (
            mock.patch.object(
                DefaultTransport, "post", side_effect=RequestException("HTTP 500 Error")
            ),
            self.assertRaises(
                ValidationError,
                msg="A network error should result in a user-friendly Error.",
            ),
        ):
            self.mde.action_confirmar_operacacao()

        # Test case for a business-level rejection from SEFAZ
        with (
            mock.patch.object(
                DefaultTransport,
                "post",
                return_value=response_confirmacao_operacao_rejeicao.encode("utf-8"),
            ),
            self.assertRaises(
                ValidationError,
                msg="A SEFAZ rejection should result in a user-friendly Error.",
            ),
        ):
            self.mde.action_confirmar_operacacao()

    @mock.patch.object(MDe, "action_ciencia_emissao", return_value=None)
    def test_download_documents(self, mock_ciencia):
        """Test downloading XMLs for one or more MDE records."""
        mde_ids = self.mde + self.mde.copy()

        # The download action itself triggers a new DFe search to get the full XML.
        # We mock this call to return the full document.
        with mock.patch.object(
            DefaultTransport,
            "post",
            return_value=response_sucesso_multiplos.encode("utf-8"),
        ):
            result_single = self.mde.action_download_xml()
            result_multiple = mde_ids.action_download_xml()

        attachment_single = self.get_attachment_from_result(result_single)
        attachment_multiple = self.get_attachment_from_result(result_multiple)

        self.assertTrue(attachment_single)
        self.assertEqual(attachment_single, self.mde.attachment_id)
        self.assertTrue(attachment_multiple)
        self.assertEqual(attachment_multiple.name, "attachments.tar.gz")

    def get_attachment_from_result(self, result):
        """Helper to extract the attachment record from the download action result."""
        # The URL is in the format /web/content/{attachment_id}/{filename}
        url_parts = result["url"].split("/")
        # e.g., ['', 'web', 'content', '591', 'filename.xml?download=true']
        self.assertGreaterEqual(len(url_parts), 4, "URL format seems incorrect.")
        self.assertEqual(url_parts[1], "web")
        self.assertEqual(url_parts[2], "content")

        attachment_id = int(url_parts[3])
        return self.env["ir.attachment"].browse(attachment_id)
