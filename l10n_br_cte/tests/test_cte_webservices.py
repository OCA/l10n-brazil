# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from types import SimpleNamespace
from unittest import mock

from erpbrasil.assinatura import misc
from erpbrasil.edoc.cte import CTe as EdocCTe

from odoo.addons.l10n_br_cte.models.document import CTe
from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_REJEITADA,
)

from .test_cte_serialize import TestCTeSerialize

_logger = logging.getLogger(__name__)


def _fake_process(cte_status, motive, webservice="cteRecepcaoSinc"):
    """Build an object shaped like erpbrasil.edoc.cte's response, as consumed
    by CTe._eletronic_document_send / update_status_cte."""
    inf_prot = SimpleNamespace(
        cStat=cte_status,
        xMotivo=motive,
        nProt="135260000000001",
        chCTe="",
        dhRecbto="2026-07-09T10:00:00-03:00",
    )
    return SimpleNamespace(
        webservice=webservice,
        envio_xml=b"",
        processo_xml=b"<cteProc/>",
        protocolo=SimpleNamespace(infProt=inf_prot),
        resposta=SimpleNamespace(cStat=cte_status, xMotivo=motive),
    )


class TestCTeWebServices(TestCTeSerialize):
    @classmethod
    def setUpClass(cls):
        super().setUpClass(
            cte_list=[
                {"record_ref": "l10n_br_cte.demo_cte_lc_modal_rodoviario"},
            ]
        )
        cls.cte = cls.cte_list[0]["cte"]
        certificate_file = misc.create_fake_certificate_file(
            valid=True,
            passwd="123456",
            issuer="EMISSOR A TESTE",
            country="BR",
            subject="CERTIFICADO VALIDO TESTE",
        )
        certificate = cls.env["l10n_br_fiscal.certificate"].create(
            {
                "type": "nf-e",
                "subtype": "a1",
                "password": "123456",
                "file": certificate_file,
            }
        )
        cls.cte.company_id.certificate_nfe_id = certificate

    def test_edoc_processor_returns_cte(self):
        """_edoc_processor builds a real erpbrasil CT-e processor for the record."""
        processor = self.cte._edoc_processor()
        self.assertIsInstance(processor, EdocCTe)
        self.assertEqual(str(processor.versao), self.cte.cte_version)
        self.assertEqual(str(processor.ambiente), self.cte.cte_environment)

    def test_document_send_authorized(self):
        """A SEFAZ authorization (cStat 100) drives the document to AUTORIZADA."""
        with mock.patch.object(
            EdocCTe,
            "processar_documento",
            side_effect=lambda *a, **k: iter(
                [_fake_process("100", "Autorizado o uso do CT-e")]
            ),
        ), mock.patch.object(CTe, "_cte_response_add_proc"):
            self.cte.action_document_send()
        self.assertEqual(self.cte.state_edoc, SITUACAO_EDOC_AUTORIZADA)
        self.assertEqual(self.cte.status_code, "100")

    def test_document_send_rejected(self):
        """A SEFAZ rejection (cStat 999) drives the document to REJEITADA."""
        with mock.patch.object(
            EdocCTe,
            "processar_documento",
            side_effect=lambda *a, **k: iter(
                [_fake_process("999", "Rejeicao: erro de schema")]
            ),
        ):
            self.cte.action_document_send()
        self.assertEqual(self.cte.state_edoc, SITUACAO_EDOC_REJEITADA)
        self.assertEqual(self.cte.status_code, "999")
