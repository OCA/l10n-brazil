# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from unittest.mock import patch

from erpbrasil.assinatura import misc
from nfelib.gnre.bindings.v2_0.lote_gnre_recibo_v1_00 import TretLoteGnre
from nfelib.gnre.bindings.v2_0.lote_gnre_result_v2_00 import (
    GuiaSituacaoGuia,
    TresultLoteGnre,
)

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

LOGGER = "odoo.addons.l10n_br_gnre.models.document"
RECEIPT = "26112800000001"
BAR_CODE = "8" * 44
DIGITABLE_LINE = "8" * 48
PIX = "00020101021226" + "9" * 100
PDF = b"%PDF-1.4 guia de teste"

Guia = TresultLoteGnre.Resultado.Guia

SOAP12 = "http://www.w3.org/2003/05/soap-envelope"
GNRE_NS = "http://www.gnre.pe.gov.br"


def soap_answer(wrapper, service, payload):
    """A SOAP 1.2 answer of the portal carrying the payload as an element."""
    payload = payload.replace(">", f' xmlns="{GNRE_NS}">', 1)
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<soapenv:Envelope xmlns:soapenv="{SOAP12}"><soapenv:Body>'
        f'<ns1:{wrapper} xmlns:ns1="http://www.gnre.pe.gov.br/webservice/{service}">'
        f"{payload}</ns1:{wrapper}></soapenv:Body></soapenv:Envelope>"
    ).encode()


class FakeGnreClient:
    """Stand-in for the nfelib client: tests never reach the portal."""

    def __init__(self, receipt=None, results=None, error=None):
        self.receipt = receipt
        self.results = list(results or [])
        self.error = error
        self.sent = []
        self.queries = []
        self.last_request_xml = "<envio/>"
        self.last_response_xml = "<retorno/>"

    def envia_lote(self, lote):
        if self.error:
            raise self.error
        self.sent.append(lote)
        return self.receipt

    def consulta_lote(self, numero_recibo, incluir_pdf_guias=False):
        if self.error:
            raise self.error
        self.queries.append((numero_recibo, incluir_pdf_guias))
        return self.results.pop(0)


def receipt(code="100", number=RECEIPT):
    return TretLoteGnre(
        situacaoRecepcao=TretLoteGnre.SituacaoRecepcao(
            codigo=code, descricao="Lote recebido com sucesso"
        ),
        recibo=TretLoteGnre.Recibo(
            numero=number,
            dataHoraRecibo="2026-11-28 10:00:00",
            tempoEstimadoProc=1,
        )
        if code == "100"
        else None,
    )


def result(code="402", guides=None, pdf=None):
    return TresultLoteGnre(
        numeroRecibo=RECEIPT,
        situacaoProcess=TresultLoteGnre.SituacaoProcess(
            codigo=code, descricao=f"Situacao {code}"
        ),
        resultado=TresultLoteGnre.Resultado(
            guia=guides or [],
            pdfGuias=base64.b64encode(pdf).decode() if pdf else None,
        )
        if guides is not None
        else None,
    )


def processed_guide(state="SP", amount="170.00"):
    return Guia(
        situacaoGuia=GuiaSituacaoGuia.VALUE_0,
        ufFavorecida=state,
        valorGNRE=amount,
        linhaDigitavel=DIGITABLE_LINE,
        codigoBarras=BAR_CODE,
        qrcodePayload=PIX,
        dataLimitePagamento="2026-08-10",
    )


@tagged("post_install", "-at_install")
class TestGnreTransmission(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.state_sp = cls.env.ref("base.state_br_sp")
        cls.company.partner_id.write(
            {
                "vat": "99.001.100/2200-51",
                "l10n_br_ie_code": "633.606.400.022",
                "legal_name": "Empresa Emitente de Testes LTDA",
                "state_id": cls.state_sp.id,
            }
        )
        cls.tax_group = cls.env.ref("l10n_br_fiscal.tax_group_icmsst")
        cls.document_type_nfe = cls.env["l10n_br_fiscal.document.type"].search(
            [("code", "=", "55")], limit=1
        )
        cls.config = cls.env["l10n_br_gnre.state.config"].create(
            {
                "company_id": cls.company.id,
                "fiscal_state_id": cls.state_sp.id,
                "tax_group_id": cls.tax_group.id,
                "revenue_code": "100099",
                "mode": "document",
                "due_days": 10,
            }
        )
        cls.document_model = cls.env.registry["l10n_br_fiscal.document"]

    def _create_guide(
        self, key="35260799001100220051550010000010001000010008", number="1000"
    ):
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company.id,
                "document_type_id": self.document_type_nfe.id,
                "document_serie": "1",
                "document_number": number,
                "document_date": "2026-07-15",
                "document_key": key,
            }
        )
        obligation = self.env["l10n_br_gnre.obligation"].create(
            {
                "company_id": self.company.id,
                "document_id": document.id,
                "config_id": self.config.id,
                "fiscal_state_id": self.state_sp.id,
                "tax_group_id": self.tax_group.id,
                "revenue_code": "100099",
                "amount_principal": 150.0,
                "amount_fcp": 20.0,
                "period_ref": "072026",
                "date_due": "2026-08-10",
            }
        )
        return self.env["l10n_br_fiscal.document"]._create_gnre_guide(obligation)

    def _patch_client(self, client):
        return patch.object(self.document_model, "_gnre_client", lambda records: client)

    def test_transmit_keeps_the_receipt(self):
        guide = self._create_guide()
        client = FakeGnreClient(receipt=receipt())
        with self._patch_client(client):
            self.assertTrue(guide.action_gnre_transmit())

        self.assertEqual(guide.gnre_transmission_state, "sent")
        self.assertEqual(guide.gnre_receipt_number, RECEIPT)
        self.assertEqual(guide.gnre_status_code, "100")
        self.assertIn("TLote_GNRE", client.sent[0])
        attachments = self.env["ir.attachment"].search(
            [("res_model", "=", guide._name), ("res_id", "=", guide.id)]
        )
        self.assertEqual(len(attachments), 2, "o XML de envio e o de retorno")

    def test_lote_carries_every_selected_guide(self):
        first = self._create_guide()
        second = self._create_guide(
            "35260799001100220051550010000010002000010006", number="1001"
        )
        guides = first | second
        client = FakeGnreClient(receipt=receipt())
        with self._patch_client(client):
            guides.action_gnre_transmit()

        self.assertEqual(client.sent[0].count("<TDadosGNRE"), 2)
        self.assertEqual(guides.mapped("gnre_lot_position"), [0, 1])

    def _three_guides(self):
        guides = self.env["l10n_br_fiscal.document"]
        for index, key in enumerate(
            (
                "35260799001100220051550010000010001000010008",
                "35260799001100220051550010000010002000010006",
                "35260799001100220051550010000010003000010004",
            )
        ):
            guides |= self._create_guide(key, number=str(1000 + index))
        return guides

    def test_guides_are_split_by_the_guide_limit(self):
        """No máximo 50 guias por lote: acima disso, um lote por fatia."""
        guides = self._three_guides()
        client = FakeGnreClient(receipt=receipt())
        with (
            self._patch_client(client),
            patch(
                "odoo.addons.l10n_br_gnre.models.document.GNRE_MAX_GUIDES_PER_LOT", 2
            ),
        ):
            self.assertTrue(guides.action_gnre_transmit())

        self.assertEqual([lote.count("<TDadosGNRE") for lote in client.sent], [2, 1])
        self.assertEqual(guides.mapped("gnre_lot_position"), [0, 1, 0])

    def test_guides_are_split_by_the_item_limit(self):
        """No máximo 300 itens por lote, somando os itens das guias."""
        guides = self._three_guides()
        client = FakeGnreClient(receipt=receipt())
        with (
            self._patch_client(client),
            patch("odoo.addons.l10n_br_gnre.models.document.GNRE_MAX_ITEMS_PER_LOT", 1),
        ):
            guides.action_gnre_transmit()

        self.assertEqual(len(client.sent), 3)

    def test_refused_reception_is_recorded_not_raised(self):
        guide = self._create_guide()
        client = FakeGnreClient(receipt=receipt(code="102"))
        with self._patch_client(client):
            guide.action_gnre_transmit()

        self.assertEqual(guide.gnre_transmission_state, "rejected")
        self.assertEqual(guide.gnre_status_code, "102")
        self.assertFalse(guide.gnre_receipt_number)

    def test_communication_error_is_recorded(self):
        guide = self._create_guide()
        client = FakeGnreClient(error=ConnectionError("portal fora do ar"))
        with self._patch_client(client), self.assertLogs(LOGGER, "WARNING"):
            self.assertFalse(guide.action_gnre_transmit())

        self.assertEqual(guide.gnre_transmission_state, "rejected")
        self.assertIn("portal fora do ar", guide.gnre_status_message)

    def test_rejected_guide_can_be_sent_again(self):
        guide = self._create_guide()
        with self._patch_client(FakeGnreClient(receipt=receipt(code="102"))):
            guide.action_gnre_transmit()
        with self._patch_client(FakeGnreClient(receipt=receipt())):
            guide.action_gnre_transmit()

        self.assertEqual(guide.gnre_transmission_state, "sent")

    def test_nothing_to_transmit(self):
        guide = self._create_guide()
        with self._patch_client(FakeGnreClient(receipt=receipt())):
            guide.action_gnre_transmit()
        with self.assertRaises(UserError):
            guide.action_gnre_transmit()

    def test_lote_cannot_mix_companies(self):
        guide = self._create_guide()
        other = guide.copy(
            {"company_id": self.env["res.company"].create({"name": "Outra"}).id}
        )
        with self.assertRaises(UserError):
            (guide | other).action_gnre_transmit()

    def test_lote_above_the_size_limit_is_refused(self):
        guide = self._create_guide()
        with patch(
            "odoo.addons.l10n_br_gnre.models.document.GNRE_MAX_MESSAGE_SIZE",
            10,
        ):
            with self.assertRaises(UserError):
                guide.action_gnre_transmit()

    def _sent_guide(self):
        guide = self._create_guide()
        with self._patch_client(FakeGnreClient(receipt=receipt())):
            guide.action_gnre_transmit()
        return guide

    def test_processed_result_fills_the_payment_data(self):
        guide = self._sent_guide()
        client = FakeGnreClient(results=[result(guides=[processed_guide()], pdf=PDF)])
        with self._patch_client(client):
            guide.action_gnre_check_result()

        self.assertEqual(client.queries, [(RECEIPT, True)])
        self.assertEqual(guide.gnre_transmission_state, "processed")
        self.assertEqual(guide.gnre_bar_code, BAR_CODE)
        self.assertEqual(guide.gnre_digitable_line, DIGITABLE_LINE)
        self.assertEqual(guide.gnre_pix_payload, PIX)
        self.assertEqual(guide.gnre_payment_due, "2026-08-10")
        self.assertEqual(guide.gnre_pdf_id.raw, PDF)
        self.assertEqual(guide.gnre_obligation_ids.state, "transmitted")
        action = guide.action_gnre_download_pdf()
        self.assertIn(str(guide.gnre_pdf_id.id), action["url"])

    def test_waiting_lot_keeps_the_guide_sent(self):
        guide = self._sent_guide()
        with self._patch_client(FakeGnreClient(results=[result(code="401")])):
            guide.action_gnre_check_result()

        self.assertEqual(guide.gnre_transmission_state, "sent")
        self.assertEqual(guide.gnre_status_code, "401")

    def test_lot_error_marks_the_guide_rejected(self):
        guide = self._sent_guide()
        with self._patch_client(
            FakeGnreClient(results=[result(code="404", guides=[])])
        ):
            guide.action_gnre_check_result()

        self.assertEqual(guide.gnre_transmission_state, "rejected")

    def test_guide_pending_in_the_portal(self):
        guide = self._sent_guide()
        pending = processed_guide()
        pending.situacaoGuia = GuiaSituacaoGuia.VALUE_4
        with self._patch_client(
            FakeGnreClient(results=[result(code="403", guides=[pending])])
        ):
            guide.action_gnre_check_result()

        self.assertEqual(guide.gnre_transmission_state, "pending")
        self.assertEqual(guide.gnre_obligation_ids.state, "grouped")

    def test_guide_rejected_by_the_state_keeps_the_reasons(self):
        guide = self._sent_guide()
        rejected = Guia(
            situacaoGuia=GuiaSituacaoGuia.VALUE_2,
            ufFavorecida="SP",
            valorGNRE="170.00",
            motivosRejeicao=Guia.MotivosRejeicao(
                motivo=[
                    Guia.MotivosRejeicao.Motivo(
                        codigo="209",
                        descricao="Informe o endereço do emitente!",
                        campo="endereco",
                    )
                ]
            ),
        )
        with self._patch_client(FakeGnreClient(results=[result(guides=[rejected])])):
            guide.action_gnre_check_result()

        self.assertEqual(guide.gnre_transmission_state, "rejected")
        self.assertIn("209", guide.gnre_rejection)
        self.assertIn("(endereco)", guide.gnre_rejection)
        self.assertEqual(guide.gnre_obligation_ids.state, "grouped")

    def test_result_is_matched_by_state_and_amount(self):
        first = self._create_guide()
        second = self._create_guide(
            "35260799001100220051550010000010002000010006", number="1001"
        )
        second.gnre_obligation_ids.amount_principal = 250.0
        guides = first | second
        with self._patch_client(FakeGnreClient(receipt=receipt())):
            guides.action_gnre_transmit()
        # The portal answers the second guide first.
        answer = result(
            guides=[processed_guide(amount="270.00"), processed_guide()],
        )
        with self._patch_client(FakeGnreClient(results=[answer])):
            guides.action_gnre_check_result()

        self.assertEqual(set(guides.mapped("gnre_transmission_state")), {"processed"})

    def test_guide_missing_from_the_result_stays_pending(self):
        guide = self._sent_guide()
        with self._patch_client(
            FakeGnreClient(results=[result(guides=[processed_guide(state="RJ")])])
        ):
            guide.action_gnre_check_result()

        self.assertEqual(guide.gnre_transmission_state, "pending")

    def test_query_error_is_kept_for_the_next_check(self):
        guide = self._sent_guide()
        client = FakeGnreClient(error=TimeoutError("sem resposta"))
        with self._patch_client(client), self.assertLogs(LOGGER, "WARNING"):
            guide.action_gnre_check_result()

        self.assertEqual(guide.gnre_transmission_state, "sent")
        self.assertIn("sem resposta", guide.gnre_status_message)

    def test_nothing_to_check(self):
        guide = self._create_guide()
        with self.assertRaises(UserError):
            guide.action_gnre_check_result()

    def test_download_without_pdf_is_refused(self):
        guide = self._create_guide()
        with self.assertRaises(UserError):
            guide.action_gnre_download_pdf()

    def test_cron_checks_the_waiting_lots(self):
        guide = self._sent_guide()
        client = FakeGnreClient(results=[result(guides=[processed_guide()])])
        with self._patch_client(client):
            self.env["l10n_br_fiscal.document"]._cron_gnre_check_results()

        self.assertEqual(guide.gnre_transmission_state, "processed")

    def test_client_uses_the_company_certificate_and_environment(self):
        guide = self._create_guide()
        self.company.gnre_environment = "1"
        pkcs12 = misc.create_fake_certificate_file(
            valid=True,
            passwd="senha",
            issuer="EMISSOR TESTE",
            country="BR",
            subject="EMPRESA EMITENTE DE TESTES",
        )
        certificate = self.env["l10n_br_fiscal.certificate"].create(
            {"type": "e-cnpj", "subtype": "a1", "password": "senha", "file": pkcs12}
        )
        self.company.write(
            {"certificate_nfe_id": False, "certificate_ecnpj_id": certificate.id}
        )
        # The company certificate is computed without dependencies.
        self.company.invalidate_recordset(["certificate"])
        with patch("nfelib.gnre.client.v2_0.GnreClient") as client_class:
            guide._gnre_client()

        client_class.assert_called_once()
        kwargs = client_class.call_args.kwargs
        self.assertEqual(kwargs["ambiente"], "1")
        self.assertEqual(kwargs["pkcs12_password"], "senha")
        self.assertEqual(
            base64.b64decode(kwargs["pkcs12_data"]), base64.b64decode(pkcs12)
        )

    def test_end_to_end_with_the_nfelib_client(self):
        """The real nfelib client builds the envelope; only HTTP is faked.

        This is the path a real transmission takes: the lote rendered by Odoo
        goes inside the SOAP 1.2 envelope of the client, the answer of the
        portal is parsed by the client and lands on the guide.
        """
        from nfelib.gnre.client.v2_0 import GnreClient

        guide = self._create_guide()
        client = GnreClient(
            ambiente="2",
            pkcs12_data=b"fake",
            pkcs12_password="",
            fake_certificate=True,
        )
        answers = [
            soap_answer(
                "processarResponse",
                "GnreLoteRecepcao",
                "<TRetLote_GNRE><ambiente>2</ambiente><situacaoRecepcao>"
                "<codigo>100</codigo><descricao>Lote recebido com sucesso"
                "</descricao></situacaoRecepcao><recibo>"
                f"<numero>{RECEIPT}</numero>"
                "<dataHoraRecibo>2026-11-28 10:00:00</dataHoraRecibo>"
                "<tempoEstimadoProc>1</tempoEstimadoProc></recibo>"
                "</TRetLote_GNRE>",
            ),
            soap_answer(
                "consultarResponse",
                "GnreResultadoLote",
                "<TResultLote_GNRE><ambiente>2</ambiente>"
                f"<numeroRecibo>{RECEIPT}</numeroRecibo><situacaoProcess>"
                "<codigo>402</codigo><descricao>Lote processado com sucesso"
                "</descricao></situacaoProcess><resultado>"
                '<guia versao="2.00"><situacaoGuia>0</situacaoGuia>'
                "<ufFavorecida>SP</ufFavorecida><tipoGnre>0</tipoGnre>"
                "<valorGNRE>170.00</valorGNRE>"
                f"<linhaDigitavel>{DIGITABLE_LINE}</linhaDigitavel>"
                f"<codigoBarras>{BAR_CODE}</codigoBarras></guia>"
                f"<pdfGuias>{base64.b64encode(PDF).decode()}</pdfGuias>"
                "</resultado></TResultLote_GNRE>",
            ),
        ]
        sent = []

        def post(location, data, headers):
            sent.append((location, data, headers))
            return answers.pop(0)

        with self._patch_client(client), patch.object(client, "_post", post):
            guide.action_gnre_transmit()
            guide.action_gnre_check_result()

        location, envelope, headers = sent[0]
        self.assertEqual(
            location,
            "https://www.testegnre.pe.gov.br/gnreWS/services/GnreLoteRecepcao",
        )
        self.assertIn("application/soap+xml", headers["Content-Type"])
        self.assertIn("<versaoDados>2.00</versaoDados>", envelope)
        self.assertIn("35260799001100220051550010000010001000010008", envelope)
        self.assertEqual(guide.gnre_receipt_number, RECEIPT)
        self.assertEqual(guide.gnre_transmission_state, "processed")
        self.assertEqual(guide.gnre_digitable_line, DIGITABLE_LINE)
        self.assertEqual(guide.gnre_pdf_id.raw, PDF)
