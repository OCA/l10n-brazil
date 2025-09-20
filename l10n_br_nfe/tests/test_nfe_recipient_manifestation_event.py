# Copyright (C) 2023 - TODAY Felipe Zago - KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# pylint: disable=line-too-long

from unittest import mock

from erpbrasil.edoc.resposta import analisar_retorno_raw
from nfelib.nfe.ws.edoc_legacy import DocumentoElectronicoAdapter
from nfelib.v4_00 import retEnvEvento

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_br_fiscal_dfe.tests.test_dfe import mocked_post_success_multiple

response_confirmacao_operacao = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"><retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote /><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>135</cStat><retEvento versao="1.00"><infEvento><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>135</cStat><xMotivo>Teste Confirmação da Operação.</xMotivo><chNFe>31201010588201000105550010038421171838422178</chNFe><tpEvento>210200</tpEvento><xEvento>Confirmacao de Operacao registrada</xEvento><nSeqEvento>1</nSeqEvento><CNPJDest>81583054000129</CNPJDest><dhRegEvento>2023-07-10T10:00:00-03:00</dhRegEvento></infEvento></retEvento></retEnvEvento></nfeResultMsg></soap:Body></soap:Envelope>"""  # noqa: E501

response_confirmacao_operacao_rejeicao = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"><retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote /><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>494</cStat><retEvento versao="1.00"><infEvento><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>494</cStat><xMotivo>Rejeição: Chave de Acesso inexistente</xMotivo><chNFe>31201010588201000105550010038421171838422178</chNFe><tpEvento>210200</tpEvento><xEvento>Confirmacao de Operacao registrada</xEvento><nSeqEvento>1</nSeqEvento><CNPJDest>81583054000129</CNPJDest><dhRegEvento>2023-07-10T10:00:00-03:00</dhRegEvento></infEvento></retEvento></retEnvEvento></nfeResultMsg></soap:Body></soap:Envelope>"""  # noqa: E501

response_ciencia_operacao = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"><retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote /><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>135</cStat><retEvento versao="1.00"><infEvento><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>135</cStat><xMotivo>Teste Ciência da Operação.</xMotivo><chNFe>31201010588201000105550010038421171838422178</chNFe><tpEvento>210210</tpEvento><xEvento>Ciencia da Operacao registrada</xEvento><nSeqEvento>1</nSeqEvento><CNPJDest>81583054000129</CNPJDest><dhRegEvento>2023-07-10T10:00:00-03:00</dhRegEvento></infEvento></retEvento></retEnvEvento></nfeResultMsg></soap:Body></soap:Envelope>"""  # noqa: E501

response_desconhecimento_operacao = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"><retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote /><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>135</cStat><retEvento versao="1.00"><infEvento><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>135</cStat><xMotivo>Teste Desconhecimento da Operação.</xMotivo><chNFe>31201010588201000105550010038421171838422178</chNFe><tpEvento>210220</tpEvento><xEvento>Desconhecimento da Operacao registrada</xEvento><nSeqEvento>1</nSeqEvento><CNPJDest>81583054000129</CNPJDest><dhRegEvento>2023-07-10T10:00:00-03:00</dhRegEvento></infEvento></retEvento></retEnvEvento></nfeResultMsg></soap:Body></soap:Envelope>"""  # noqa: E501

response_operacao_nao_realizada = """<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soap:Body><nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"><retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote /><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>135</cStat><retEvento versao="1.00"><infEvento><tpAmb>2</tpAmb><verAplic>SVRS202305251555</verAplic><cStat>135</cStat><xMotivo>Teste Operação não Realizada.</xMotivo><chNFe>31201010588201000105550010038421171838422178</chNFe><tpEvento>210240</tpEvento><xEvento>Operacao nao Realizada registrada</xEvento><nSeqEvento>1</nSeqEvento><CNPJDest>81583054000129</CNPJDest><dhRegEvento>2023-07-10T10:00:00-03:00</dhRegEvento></infEvento></retEvento></retEnvEvento></nfeResultMsg></soap:Body></soap:Envelope>"""  # noqa: E501


class FakeRetorno:
    def __init__(self, text, status_code=200):
        self.text = text
        self.content = text.encode("utf-8")
        self.status_code = status_code

    def raise_for_status(self):
        pass


def mocked_post_confirmacao(*args, **kwargs):
    return analisar_retorno_raw(
        "nfeRecepcaoEvento",
        object(),
        b"<fake_post/>",
        FakeRetorno(response_confirmacao_operacao),
        retEnvEvento,
    )


def mocked_post_confirmacao_status_code_error(*args, **kwargs):
    return analisar_retorno_raw(
        "nfeRecepcaoEvento",
        object(),
        b"<fake_post/>",
        FakeRetorno(response_confirmacao_operacao, status_code="500"),
        retEnvEvento,
    )


def mocked_post_confirmacao_invalid_status_error(*args, **kwargs):
    return analisar_retorno_raw(
        "nfeRecepcaoEvento",
        object(),
        b"<fake_post/>",
        FakeRetorno(response_confirmacao_operacao_rejeicao),
        retEnvEvento,
    )


def mocked_post_ciencia(*args, **kwargs):
    return analisar_retorno_raw(
        "nfeRecepcaoEvento",
        object(),
        b"<fake_post/>",
        FakeRetorno(response_ciencia_operacao),
        retEnvEvento,
    )


def mocked_post_desconhecimento(*args, **kwargs):
    return analisar_retorno_raw(
        "nfeRecepcaoEvento",
        object(),
        b"<fake_post/>",
        FakeRetorno(response_desconhecimento_operacao),
        retEnvEvento,
    )


def mocked_post_nao_realizada(*args, **kwargs):
    return analisar_retorno_raw(
        "nfeRecepcaoEvento",
        object(),
        b"<fake_post/>",
        FakeRetorno(response_operacao_nao_realizada),
        retEnvEvento,
    )


class TestMDe(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        dfe_monitor = cls.env["l10n_br_fiscal.dfe_monitor"].create(
            {
                "last_nsu": "000000000000001",
                "company_id": cls.env.ref("l10n_br_base.empresa_simples_nacional").id,
            }
        )
        with mock.patch.object(
            DocumentoElectronicoAdapter,
            "_post",
            side_effect=mocked_post_success_multiple,
        ):
            dfe_monitor.search_documents()

            cls.dfe = dfe_monitor.dfe_ids[0]
            cls.mde_create = cls.env[
                "l10n_br_nfe.recipient_manifestation_event"
            ].create(
                {
                    "company_id": cls.dfe.company_id.id,
                    "key": cls.dfe.key,
                    "document_number": cls.dfe.document_number,
                    "event_type": "ciente",
                    "status": "rascunho",
                    "dfe_access_key_id": cls.dfe.dfe_access_key_id.id,
                    "mde_document_type": "mde_nfe",
                }
            )
            cls.mde_id = cls.mde_create

    def test_events_success(self):
        with mock.patch.object(
            DocumentoElectronicoAdapter,
            "_post",
            side_effect=mocked_post_ciencia,
        ):
            self.mde_id.event_type_selection = "ciente"
            self.mde_id.action_confirm_selection()
            self.assertEqual(self.mde_id.event_type, "ciente")
            self.assertEqual(
                self.mde_id.display_name, "31201010588201000105550010038421171838422178"
            )

        with mock.patch.object(
            DocumentoElectronicoAdapter,
            "_post",
            side_effect=mocked_post_confirmacao,
        ):
            self.mde_id.event_type_selection = "confirmado"
            self.mde_id.action_confirm_selection()
            self.assertEqual(self.mde_id.event_type, "confirmado")

        with mock.patch.object(
            DocumentoElectronicoAdapter,
            "_post",
            side_effect=mocked_post_desconhecimento,
        ):
            self.mde_id.event_type_selection = "desconhecido"
            self.mde_id.action_confirm_selection()
            self.assertEqual(self.mde_id.event_type, "desconhecido")

        with mock.patch.object(
            DocumentoElectronicoAdapter,
            "_post",
            side_effect=mocked_post_nao_realizada,
        ):
            self.mde_id.event_type_selection = "nao_realizado"
            self.mde_id.action_confirm_selection()
            self.assertEqual(self.mde_id.event_type, "nao_realizado")

    def test_event_error(self):
        with mock.patch.object(
            DocumentoElectronicoAdapter,
            "_post",
            side_effect=mocked_post_confirmacao_status_code_error,
        ), self.assertRaises(ValidationError):
            self.mde_id.event_type_selection = "confirmado"
            self.mde_id.action_confirm_selection()

        with mock.patch.object(
            DocumentoElectronicoAdapter,
            "_post",
            side_effect=mocked_post_confirmacao_invalid_status_error,
        ), self.assertRaises(ValidationError):
            self.mde_id.event_type_selection = "confirmado"
            self.mde_id.action_confirm_selection()

    def test_wizard_create_nfe_recipient_manifestation_event(self):
        mde_wizard = (
            self.env["nfe_recipient_manifestation_event.wizard"]
            .with_context(default_dfe_access_key_id=self.dfe.dfe_access_key_id.id)
            .create({"event_type_selection": "confirmado"})
        )
        with mock.patch.object(
            DocumentoElectronicoAdapter,
            "_post",
            side_effect=mocked_post_confirmacao,
        ):
            mde = mde_wizard.action_create_nfe_recipient_manifestation_event()

        mde = self.env["l10n_br_nfe.recipient_manifestation_event"].search(
            [("dfe_access_key_id", "=", self.dfe.dfe_access_key_id.id)]
        )

        self.assertEqual(mde[1].event_type, "confirmado")
        with mock.patch.object(
            DocumentoElectronicoAdapter,
            "_post",
            side_effect=mocked_post_confirmacao,
        ):
            mde[1].event_type_selection = "confirmado"
            mde[1].action_confirm_selection()
            self.assertEqual(mde[1].event_type, "confirmado")
