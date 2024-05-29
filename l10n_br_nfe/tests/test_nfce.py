# Copyright 2023 KMEE (Felipe Zago Rodrigues <felipe.zago@kmee.com.br>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from unittest import mock

from erpbrasil.assinatura import misc

from odoo.fields import Datetime

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    AUTORIZADO,
    SITUACAO_EDOC_A_ENVIAR,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_INUTILIZADA,
    SITUACAO_EDOC_REJEITADA,
)

from .mock_utils import nfe_mock
from .test_nfe_serialize import TestNFeExport


class TestNFCe(TestNFeExport):
    def setUp(self):
        super().setUp(nfe_list=[])

        self.document_id = self.env.ref("l10n_br_nfe.demo_nfce_same_state")

        certificate_valid = misc.create_fake_certificate_file(
            valid=True,
            passwd="123456",
            issuer="EMISSOR A TESTE",
            country="BR",
            subject="CERTIFICADO VALIDO TESTE",
        )
        certificate_id = self.env["l10n_br_fiscal.certificate"].create(
            {
                "type": "nf-e",
                "subtype": "a1",
                "password": "123456",
                "file": certificate_valid,
            }
        )
        self.document_id.company_id.certificate_nfe_id = certificate_id
        self.document_id.company_id.nfce_csc_token = "DUMMY"
        self.document_id.company_id.nfce_csc_code = "DUMMY"

        self.prepare_test_nfe(self.document_id)

    @nfe_mock({"nfeAutorizacaoLote": "retEnviNFe/autorizada.xml"})
    def test_nfce_success(self):
        self.document_id.action_document_send()

        self.assertEqual(self.document_id.state_edoc, SITUACAO_EDOC_AUTORIZADA)

        cancel_wizard = (
            self.env["l10n_br_fiscal.document.cancel.wizard"]
            .with_context(
                active_model="l10n_br_fiscal.document", active_id=self.document_id.id
            )
            .create(
                {
                    "document_id": self.document_id.id,
                    "justification": "Era apenas um teste.",
                }
            )
        )
        with nfe_mock({"nfeRecepcaoEvento": "retEnvEvento/nfce_cancelamento.xml"}):
            cancel_wizard.doit()

        self.assertEqual(self.document_id.state_edoc, SITUACAO_EDOC_CANCELADA)
        self.assertIsNotNone(self.document_id.cancel_event_id)
        self.assertEqual(self.document_id.cancel_event_id.state, "done")
        self.assertEqual(self.document_id.cancel_event_id.status_code, "135")
        self.assertEqual(
            self.document_id.cancel_event_id.response,
            "Evento registrado e vinculado a NF-e",
        )
        self.assertEqual(
            Datetime.to_string(self.document_id.cancel_event_id.protocol_date),
            "2023-07-05 16:52:52",
        )

    @nfe_mock({"nfeAutorizacaoLote": "retEnviNFe/rejeitada.xml"})
    def test_nfce_rejeitada(self):
        self.document_id.action_document_send()
        self.assertEqual(self.document_id.state_edoc, SITUACAO_EDOC_REJEITADA)

    @nfe_mock({"nfeAutorizacaoLote": "retEnviNFe/denegada.xml"})
    def test_nfce_denegada(self):
        self.document_id.action_document_send()
        self.assertEqual(self.document_id.state_edoc, SITUACAO_EDOC_DENEGADA)

    @nfe_mock({"nfeAutorizacaoLote": "retEnviNFe/servico_paralizado.xml"})
    def test_nfce_contingencia(self):
        self.document_id.action_document_send()
        self.assertEqual(self.document_id.state_edoc, SITUACAO_EDOC_A_ENVIAR)
        self.assertEqual(self.document_id.nfe_transmission, "9")
        self.assertIsNotNone(self.document_id.get_nfce_qrcode())

    @nfe_mock({"nfeInutilizacaoNF": "retInutNFe/nfce_inutilizacao.xml"})
    def test_inutilizar(self):
        inutilizar_wizard = (
            self.env["l10n_br_fiscal.invalidate.number.wizard"]
            .with_context(
                active_model="l10n_br_fiscal.document", active_id=self.document_id.id
            )
            .create(
                {
                    "document_id": self.document_id.id,
                    "justification": "Era apenas um teste.",
                }
            )
        )
        inutilizar_wizard.doit()

        self.assertEqual(self.document_id.state_edoc, SITUACAO_EDOC_INUTILIZADA)

    def test_atualiza_status_nfce(self):
        self.document_id._onchange_fiscal_operation_id()
        self.document_id._onchange_document_type_id()

        self.document_id._compute_nfe40_dhSaiEnt()
        self.assertFalse(self.document_id.nfe40_dhSaiEnt)

        self.document_id._inverse_nfe40_dhSaiEnt()
        self.assertFalse(self.document_id.nfe40_dhSaiEnt)

        mock_autorizada = mock.MagicMock(spec=["protocolo"])
        mock_autorizada.protocolo.infProt.cStat = AUTORIZADO[0]
        mock_autorizada.protocolo.infProt.xMotivo = "TESTE AUTORIZADO"
        mock_autorizada.protocolo.infProt.dhRecbto = datetime.now()
        mock_autorizada.processo_xml = b"dummy"
        mock_autorizada.resposta = mock.MagicMock()
        mock_autorizada.webservice = "dummy_service"
        self.document_id._nfe_update_status_and_save_data(mock_autorizada)

        self.assertEqual(self.document_id.state_edoc, SITUACAO_EDOC_AUTORIZADA)
        self.assertEqual(self.document_id.status_code, AUTORIZADO[0])
        self.assertEqual(self.document_id.status_name, "TESTE AUTORIZADO")

    def test_qrcode(self):
        old_document_type = self.document_id.document_type_id
        self.document_id.document_type_id = False

        qr_code = self.document_id.get_nfce_qrcode()
        qr_code_url = self.document_id.get_nfce_qrcode_url()
        self.assertIsNone(qr_code)
        self.assertIsNone(qr_code_url)

        self.document_id.document_type_id = old_document_type
        qr_code = self.document_id.get_nfce_qrcode()
        qr_code_url = self.document_id.get_nfce_qrcode_url()
        self.assertIsNotNone(qr_code)
        self.assertIsNotNone(qr_code_url)

    @nfe_mock({"nfeAutorizacaoLote": "retEnviNFe/autorizada.xml"})
    def test_prepare_nfce_payment(self):
        amount = self.document_id.amount_financial_total / 2
        self.document_id.nfe40_detPag = [
            (5, 0, 0),
            (
                0,
                0,
                {
                    "nfe40_indPag": "0",
                    "nfe40_tPag": "99",
                    "nfe40_vPag": amount,
                },
            ),
            (
                0,
                0,
                {
                    "nfe40_indPag": "0",
                    "nfe40_tPag": "99",
                    "nfe40_vPag": amount,
                },
            ),
        ]

        self.document_id._eletronic_document_send()

        others_pag = self.document_id.nfe40_detPag.filtered(
            lambda p: p.nfe40_tPag == "99"
        )
        self.assertTrue(all(pag.nfe40_xPag == "Outros" for pag in others_pag))

    def test_view_nfce_pdf(self):
        action_pdf = self.document_id.view_pdf()
        report_action = action_pdf["context"]["report_action"]

        self.assertEqual(report_action["report_file"], "l10n_br_nfe.danfe_nfce")
        self.assertEqual(report_action["report_name"], "l10n_br_nfe.report_danfe_nfce")
        self.assertEqual(report_action["report_type"], "qweb-html")

    def test_prepare_nfce_values_for_pdf(self):
        line_values = self.document_id._prepare_nfce_danfe_line_values()

        line1 = line_values[0]
        self.assertEqual(line1["product_quantity"], 1)
        self.assertEqual(line1["product_unit_value"], 320)
        self.assertEqual(line1["product_unit_total"], 320)

        self.document_id.nfe40_detPag = [
            (5, 0, 0),
            (
                0,
                0,
                {
                    "nfe40_indPag": "1",
                    "nfe40_tPag": "01",
                    "nfe40_vPag": 320,
                },
            ),
        ]

        payment_values = self.document_id._prepare_nfce_danfe_payment_values()
        payment = payment_values[0]

        self.assertEqual(payment["method"], "01 - Dinheiro")
        self.assertEqual(payment["value"], 320)

    def test_compute_fiscal_document_fields(self):
        self.document_id.partner_id.is_anonymous_consumer = True
        self.document_id.partner_id.cnpj_cpf = False
        self.document_id.partner_shipping_id = self.document_id.partner_id

        self.document_id._compute_entrega_data()
        self.assertFalse(self.document_id.nfe40_entrega)

        self.document_id._compute_dest_data()
        self.assertFalse(self.document_id.nfe40_dest)
