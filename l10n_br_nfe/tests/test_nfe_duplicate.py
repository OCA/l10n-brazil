# Copyright (C) 2026 - TODAY KMEE (<https://kmee.com.br>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
from unittest import mock

from lxml import etree

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_REJEITADA,
)
from odoo.addons.l10n_br_nfe.models.document import NFe

from .mock_utils import NFeMock, load_soap_xml, mock_response
from .test_nfe_serialize import TestNFeExport

DS_NS = {"ds": "http://www.w3.org/2000/09/xmldsig#"}
OTHER_DIGEST = "AAAAAAAAAAAAAAAAAAAAAAAAAAA="
ORIGINAL_KEY_539 = "35200159594315000157550010000000021234567890"


class TestNFeDuplicate(TestNFeExport):
    def setUp(self):
        nfe_list = [
            {
                "record_ref": "l10n_br_nfe.demo_nfe_natural_icms_18_red_51_11",
                "xml_file": "NFe35200159594315000157550010000000022062777169.xml",
            },
        ]
        super().setUp(nfe_list)
        self.nfe = nfe_list[0]["nfe"]

    def _send(self, paths, consult_digest=None):
        """
        Send the NF-e with the webservices mocked by `paths`. The protocol
        query answers an authorized NF-e with the key of the document and
        the digest returned by `consult_digest(sent_digest)`.
        Return the list of the called webservices.
        """
        nfe_mock = NFeMock(paths)
        calls = []
        sent = {}

        def custom_send(operacao, *args, **kwargs):
            calls.append(operacao)
            if operacao == "nfeAutorizacaoLote":
                sent["digest"] = args[0].xpath(
                    "//ds:DigestValue/text()", namespaces=DS_NS
                )[0]
            if operacao == "nfeConsultaNF":
                content = load_soap_xml("retConsSitNFe/autorizado_duplicidade.xml")
                content = content.replace(
                    b"CHAVE_NFE", self.nfe.document_key.encode()
                ).replace(b"DIGEST_VALUE", consult_digest(sent["digest"]).encode())
                return mock_response(content)
            return nfe_mock.custom_send(operacao, *args, **kwargs)

        with nfe_mock, mock.patch.object(NFe, "make_pdf"):
            nfe_mock.mock_send.side_effect = custom_send
            self.nfe.action_document_send()
        return calls

    def _assert_signed_proc(self):
        """The nfeProc joins the signed NF-e sent and the recovered protocol."""
        proc = base64.b64decode(self.nfe.authorization_file_id.datas)
        tree = etree.fromstring(proc)
        self.assertEqual(etree.QName(tree).localname, "nfeProc")
        self.assertEqual(
            tree.xpath("//*[local-name()='nProt']/text()"), ["126200000020426"]
        )
        self.assertEqual(
            tree.xpath("//ds:DigestValue/text()", namespaces=DS_NS),
            tree.xpath("//*[local-name()='digVal']/text()"),
        )

    def _last_message(self):
        messages = self.nfe.message_ids.filtered(
            lambda m: "SEFAZ rejection" in (m.body or "")
        )
        return messages.sorted("id")[-1:].body or ""

    def test_204_same_digest_recovers_protocol(self):
        calls = self._send(
            {
                "nfeAutorizacaoLote": "retEnviNFe/lote_recebido.xml",
                "nfeRetAutorizacaoLote": "retConsReciNFe/duplicidade.xml",
            },
            consult_digest=lambda sent_digest: sent_digest,
        )
        self.assertIn("nfeConsultaNF", calls)
        self.assertEqual(self.nfe.state_edoc, SITUACAO_EDOC_AUTORIZADA)
        self.assertEqual(self.nfe.status_code, "100")
        self.assertEqual(self.nfe.authorization_protocol, "126200000020426")
        self._assert_signed_proc()
        self.assertIn("126200000020426", self._last_message())
        self.assertIn(self.nfe.document_key, self._last_message())

    def test_204_same_digest_sync_recovers_protocol(self):
        """In sync mode the digest is read from the request of the process."""
        self.nfe.company_id.nfe_enable_sync_transmission = True
        calls = self._send(
            {"nfeAutorizacaoLote": "retEnviNFe/duplicidade.xml"},
            consult_digest=lambda sent_digest: sent_digest,
        )
        self.assertIn("nfeConsultaNF", calls)
        self.assertEqual(self.nfe.state_edoc, SITUACAO_EDOC_AUTORIZADA)
        self.assertEqual(self.nfe.authorization_protocol, "126200000020426")
        self._assert_signed_proc()

    def test_204_other_digest_keeps_rejection(self):
        calls = self._send(
            {
                "nfeAutorizacaoLote": "retEnviNFe/lote_recebido.xml",
                "nfeRetAutorizacaoLote": "retConsReciNFe/duplicidade.xml",
            },
            consult_digest=lambda sent_digest: OTHER_DIGEST,
        )
        self.assertIn("nfeConsultaNF", calls)
        self.assertEqual(self.nfe.state_edoc, SITUACAO_EDOC_REJEITADA)
        self.assertEqual(self.nfe.status_code, "204")
        self.assertFalse(self.nfe.authorization_protocol)
        self.assertEqual(self.nfe.authorization_event_id.status_code, "204")
        message = self._last_message()
        self.assertIn(self.nfe.document_key, message)
        self.assertIn("not associated", message)

    def test_539_reports_original_key(self):
        calls = self._send(
            {
                "nfeAutorizacaoLote": "retEnviNFe/lote_recebido.xml",
                "nfeRetAutorizacaoLote": (
                    "retConsReciNFe/duplicidade_chave_diferente.xml"
                ),
            },
        )
        # The original key is never queried to take its protocol.
        self.assertNotIn("nfeConsultaNF", calls)
        self.assertEqual(self.nfe.state_edoc, SITUACAO_EDOC_REJEITADA)
        self.assertEqual(self.nfe.status_code, "539")
        self.assertFalse(self.nfe.authorization_protocol)
        self.assertNotEqual(self.nfe.document_key, ORIGINAL_KEY_539)
        message = self._last_message()
        self.assertIn("539", message)
        self.assertIn(ORIGINAL_KEY_539, message)

    def test_100_does_not_query_protocol(self):
        messages = self.nfe.message_ids
        calls = self._send(
            {
                "nfeAutorizacaoLote": "retEnviNFe/lote_recebido.xml",
                "nfeRetAutorizacaoLote": "retConsReciNFe/autorizada.xml",
            },
        )
        self.assertNotIn("nfeConsultaNF", calls)
        self.assertEqual(self.nfe.state_edoc, SITUACAO_EDOC_AUTORIZADA)
        self.assertEqual(self.nfe.status_code, "100")
        self.assertEqual(self.nfe.authorization_protocol, "423002202113232")
        new_messages = (self.nfe.message_ids - messages).mapped("body")
        self.assertFalse([m for m in new_messages if "SEFAZ rejection" in m])
