# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import datetime
from html import escape
from types import SimpleNamespace
from unittest.mock import patch

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID
from erpbrasil.assinatura.certificado import Certificado
from erpbrasil.edoc.provedores.giss import NS_DS, NS_GISS, NS_SERVICO, NS_TIPOS, Giss
from lxml import etree
from xsdata.formats.dataclass.serializers import XmlSerializer

from odoo.exceptions import UserError
from odoo.tools import mute_logger

from odoo.addons.l10n_br_nfse.tests.test_fiscal_document_nfse_common import (
    TestFiscalDocumentNFSeCommon,
)

T = f"{{{NS_TIPOS}}}"
DOCUMENT = "odoo.addons.l10n_br_nfse_giss.models.document.Document"


def soap(operacao, corpo):
    return (
        '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
        f'<soap:Body><ns2:{operacao}Response xmlns:ns2="{NS_SERVICO}">'
        f"<outputXML>{escape(corpo)}</outputXML>"
        f"</ns2:{operacao}Response></soap:Body></soap:Envelope>"
    )


def mensagem(codigo, texto):
    return (
        f'<ListaMensagemRetorno xmlns="{NS_TIPOS}"><MensagemRetorno>'
        f"<Codigo>{codigo}</Codigo><Mensagem>{texto}</Mensagem>"
        "</MensagemRetorno></ListaMensagemRetorno>"
    )


def comp_nfse(numero_rps, cancelada=False):
    cancelamento = (
        '<t:NfseCancelamento versao="2.04"><t:Confirmacao>'
        "<t:DataHora>2026-11-10T11:00:00</t:DataHora></t:Confirmacao>"
        "</t:NfseCancelamento>"
        if cancelada
        else ""
    )
    return (
        f'<t:CompNfse xmlns:t="{NS_TIPOS}"><t:Nfse versao="2.04">'
        '<t:InfNfse Id="nfse55"><t:Numero>55</t:Numero>'
        "<t:CodigoVerificacao>ABC123XYZ</t:CodigoVerificacao>"
        "<t:DataEmissao>2026-11-10T10:00:05</t:DataEmissao>"
        "<t:DeclaracaoPrestacaoServico><t:InfDeclaracaoPrestacaoServico>"
        f"<t:Rps><t:IdentificacaoRps><t:Numero>{numero_rps}</t:Numero>"
        "<t:Serie>1</t:Serie><t:Tipo>1</t:Tipo></t:IdentificacaoRps></t:Rps>"
        "</t:InfDeclaracaoPrestacaoServico></t:DeclaracaoPrestacaoServico>"
        f"</t:InfNfse></t:Nfse>{cancelamento}"
        f"<t:ChaveNotaNacional>{'3' * 50}</t:ChaveNotaNacional></t:CompNfse>"
    )


def resposta(mensagem_xsd, tag, corpo):
    return f'<{tag} xmlns="{NS_GISS.format(mensagem_xsd)}">{corpo}</{tag}>'


RPS_NAO_ENCONTRADO = soap(
    "ConsultarNfsePorRps",
    resposta(
        "consultar-nfse-rps-resposta",
        "ConsultarNfseRpsResposta",
        mensagem("E4", "RPS nao encontrado"),
    ),
)
RPS_JA_CONVERTIDO = soap(
    "ConsultarNfsePorRps",
    resposta("consultar-nfse-rps-resposta", "ConsultarNfseRpsResposta", comp_nfse(50)),
)
PROTOCOLO = soap(
    "RecepcionarLoteRps",
    resposta(
        "enviar-lote-rps-resposta",
        "EnviarLoteRpsResposta",
        "<NumeroLote>50</NumeroLote><Protocolo>PROT-123</Protocolo>",
    ),
)
LOTE_RECUSADO = soap(
    "RecepcionarLoteRps",
    resposta(
        "enviar-lote-rps-resposta",
        "EnviarLoteRpsResposta",
        mensagem("E160", "Arquivo em desacordo com o XML Schema"),
    ),
)
LOTE_PROCESSADO = soap(
    "ConsultarLoteRps",
    resposta(
        "consultar-lote-rps-resposta",
        "ConsultarLoteRpsResposta",
        f"<Situacao>4</Situacao><ListaNfse>{comp_nfse(50)}</ListaNfse>",
    ),
)
LOTE_EM_FILA = soap(
    "ConsultarLoteRps",
    resposta(
        "consultar-lote-rps-resposta",
        "ConsultarLoteRpsResposta",
        "<Situacao>2</Situacao>",
    ),
)
LOTE_COM_ERRO = soap(
    "ConsultarLoteRps",
    resposta(
        "consultar-lote-rps-resposta",
        "ConsultarLoteRpsResposta",
        "<Situacao>3</Situacao>" + mensagem("E174", "RPS nao assinado"),
    ),
)
CANCELADA = soap(
    "CancelarNfse",
    resposta(
        "cancelar-nfse-resposta",
        "CancelarNfseResposta",
        f'<RetCancelamento><t:NfseCancelamento xmlns:t="{NS_TIPOS}" versao="2.04">'
        "<t:Confirmacao><t:DataHora>2026-11-10T11:00:00</t:DataHora>"
        "</t:Confirmacao></t:NfseCancelamento></RetCancelamento>",
    ),
)
CANCELAMENTO_RECUSADO = soap(
    "CancelarNfse",
    resposta(
        "cancelar-nfse-resposta",
        "CancelarNfseResposta",
        mensagem("E79", "NFS-e ja cancelada"),
    ),
)


def certificado_temporario():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    nome = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "TESTE:02244507000116")])
    agora = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(nome)
        .issuer_name(nome)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(agora - datetime.timedelta(days=1))
        .not_valid_after(agora + datetime.timedelta(days=1))
        .sign(key, hashes.SHA256())
    )
    pfx = pkcs12.serialize_key_and_certificates(
        b"teste", key, cert, None, serialization.BestAvailableEncryption(b"teste")
    )
    return Certificado(base64.b64encode(pfx), "teste")


class FakeResponse:
    def __init__(self, content):
        self.content = content.encode("utf-8")
        self.status_code = 200


class FakeSession:
    """Answers in order; the last answer repeats."""

    def __init__(self, *respostas):
        self.respostas = list(respostas)
        self.chamadas = []

    def post(self, url, data, headers, timeout):
        self.chamadas.append(
            {"url": url, "operacao": headers["SOAPAction"].rsplit("/", 1)[1]}
        )
        dados = etree.fromstring(data).find(".//nfseDadosMsg").text
        self.chamadas[-1]["dados"] = etree.fromstring(dados.encode())
        atual = self.respostas.pop(0) if len(self.respostas) > 1 else self.respostas[0]
        return FakeResponse(atual)

    @property
    def operacoes(self):
        return [chamada["operacao"] for chamada in self.chamadas]


class TestNFSeGiss(TestFiscalDocumentNFSeCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.certificado = certificado_temporario()
        cls.company.provedor_nfse = "giss"
        # Guarulhos: the production host comes from the city of the company
        cls.company.partner_id.city_id = cls.env.ref("l10n_br_base.city_3518800")
        cls.company.partner_id.state_id = cls.env.ref("base.state_br_sp")
        cls.nfse = cls.nfse_same_state
        cls.nfse.nfse_environment = "1"
        cls.nfse.document_date = datetime.datetime(2026, 11, 10, 13, 0, 0)
        cls.nfse.date_in_out = datetime.datetime(2026, 11, 10, 13, 0, 0)
        cls.line = cls.nfse.fiscal_line_ids[0]
        # ISS due where the service is provided
        cls.line.issqn_eligibility = "1"
        cls.line.issqn_fg_city_id = cls.company.partner_id.city_id
        # the data of the tax reform of a taxed service, all on the line
        cls.line.tax_classification_id = cls.env.ref(
            "l10n_br_fiscal.tax_classification_000001"
        )
        cls.line.ibs_cst_id = cls.env.ref("l10n_br_fiscal.cst_ibs_000")
        cls.line.operation_indicator_id = cls.env.ref(
            "l10n_br_fiscal.operation_indicator_030101"
        )

    def setUp(self):
        super().setUp()
        self.session = FakeSession("")
        company = self.company

        def provider(record, session=None):
            return Giss(
                SimpleNamespace(certificado=self.certificado),
                record.nfse_environment,
                int(company.partner_id.city_id.ibge_code),
                "02244507000116",
                "217351",
                session=self.session,
            )

        for target, kwargs in (
            (f"{DOCUMENT}._giss_provider", {"new": provider}),
            (
                "odoo.addons.l10n_br_nfse.models.document.Document.make_pdf",
                {"return_value": None},
            ),
            ("erpbrasil.edoc.provedores.giss.time.sleep", {"return_value": None}),
        ):
            patcher = patch(target, **kwargs)
            patcher.start()
            self.addCleanup(patcher.stop)

    def _rps(self):
        xml = XmlSerializer().render(self.nfse._serialize_nfse_giss())
        return etree.fromstring(xml.encode())

    def _send(self, *respostas):
        self.session.respostas = list(respostas)
        self.nfse.action_document_confirm()
        self.nfse.action_document_send()

    # ------------------------------------------------------------------ RPS

    def test_rps(self):
        raiz = self._rps()
        ns_envio = NS_GISS.format("enviar-lote-rps-envio")
        self.assertEqual(raiz.tag, f"{{{ns_envio}}}EnviarLoteRpsEnvio")
        lote = raiz[0]
        self.assertEqual((lote.get("Id"), lote.get("versao")), ("lote50", "2.04"))
        self.assertEqual(lote.findtext(f"{T}QuantidadeRps"), "1")
        declaracao = lote.find(f".//{T}InfDeclaracaoPrestacaoServico")
        self.assertEqual(declaracao.get("Id"), "rps50")
        self.assertEqual(
            declaracao.findtext(f"{T}Rps/{T}IdentificacaoRps/{T}Numero"), "50"
        )
        servico = declaracao.find(f"{T}Servico")
        # the item keeps the leading zero and the dot, as the city hall wants
        self.assertRegex(servico.findtext(f"{T}ItemListaServico"), r"^\d{2}\.\d{2}$")
        self.assertEqual(servico.findtext(f"{T}ExigibilidadeISS"), "1")
        self.assertEqual(servico.findtext(f"{T}CodigoMunicipio"), "3518800")
        self.assertEqual(servico.findtext(f"{T}MunicipioIncidencia"), "3518800")
        # the rate is a fraction with four decimals, never a percentage
        aliquota = servico.findtext(f"{T}Valores/{T}Aliquota")
        if aliquota:
            self.assertLess(float(aliquota), 1)
            self.assertEqual(len(aliquota.split(".")[1]), 4)
        # the approximate tax burden is mandatory in the trib group
        self.assertIsNotNone(servico.find(f"{T}Valores/{T}trib/{T}totTrib"))
        tomador = declaracao.find(f"{T}TomadorServico")
        self.assertTrue(tomador.findtext(f"{T}RazaoSocial"))
        # no signature yet: the provider signs each RPS and then the lot
        self.assertFalse(list(raiz.iter(f"{{{NS_DS}}}Signature")))

    def test_rps_without_the_tax_reform_data_has_no_ibscbs_group(self):
        self.line.tax_classification_id = False
        self.assertIsNone(self._rps().find(f".//{T}IBSCBS"))

    def test_rps_with_the_tax_reform_data(self):
        grupo = self._rps().find(f".//{T}IBSCBS")
        self.assertIsNotNone(grupo)
        self.assertEqual(grupo.findtext(f"{T}cIndOp"), "030101")
        self.assertTrue(float(grupo.findtext(f"{T}valores/{T}vBC")))
        classificacao = grupo.find(f"{T}valores/{T}trib/{T}gIBSCBS")
        self.assertEqual(classificacao.findtext(f"{T}cClassTrib"), "000001")
        self.assertEqual(grupo.findtext(f"{T}valores/{T}cLocalidadeIncid"), "3518800")

    @mute_logger("odoo.addons.l10n_br_nfse.models.document")
    def test_rps_with_partial_tax_reform_data_has_no_ibscbs_group(self):
        self.line.operation_indicator_id = False
        self.assertIsNone(self._rps().find(f".//{T}IBSCBS"))

    def test_rps_describes_every_line(self):
        self.line.name = "Frete aereo"
        self.line.copy({"name": "Armazenagem", "product_id": self.line.product_id.id})
        self.assertEqual(
            self._rps().findtext(f".//{T}Servico/{T}Discriminacao"),
            "Frete aereo\nArmazenagem",
        )

    def _abroad(self):
        self.nfse.partner_id.write(
            {
                "country_id": self.env.ref("base.us").id,
                "state_id": self.env.ref("base.state_us_10").id,
                "city_id": False,
                "city": "Miami",
                "street": "100 Fictitious Avenue",
                "street2": False,
                "zip": "33101",
                "vat": "12-3456789",
            }
        )

    def _in_dollars(self):
        return patch.object(
            type(self.nfse),
            "_nfse_foreign_currency_rate",
            return_value=(self.env.ref("base.USD"), 5.0),
        )

    def test_export_to_a_customer_abroad(self):
        self._abroad()
        self.line.issqn_eligibility = "4"
        self.nfse.nfse_foreign_trade_mode = "4"
        with self._in_dollars():
            declaracao = self._rps().find(f".//{T}InfDeclaracaoPrestacaoServico")
        tomador = declaracao.find(f"{T}TomadorServico")
        self.assertIsNone(tomador.find(f"{T}IdentificacaoTomador"))
        self.assertEqual(tomador.findtext(f"{T}NifTomador"), "12-3456789")
        exterior = tomador.find(f"{T}EnderecoExterior")
        # ISO 3166 numeric, not the BACEN code of the country (2496)
        self.assertEqual(exterior.findtext(f"{T}CodigoPais"), "0840")
        self.assertEqual(exterior.findtext(f"{T}cEndPost"), "33101")
        self.assertEqual(exterior.findtext(f"{T}xCidade"), "Miami")
        self.assertEqual(exterior.findtext(f"{T}xEstProvReg"), "Florida")
        servico = declaracao.find(f"{T}Servico")
        self.assertEqual(servico.findtext(f"{T}ExigibilidadeISS"), "4")
        self.assertEqual(servico.findtext(f"{T}CodigoMunicipio"), "9999999")
        self.assertEqual(servico.findtext(f"{T}MunicipioIncidencia"), "3518800")
        self.assertEqual(servico.findtext(f"{T}CodigoPais"), "0840")
        # in reais by the invoice rate, and in dollars in the foreign trade group
        self.assertEqual(
            float(servico.findtext(f"{T}Valores/{T}ValorServicos")),
            round(self.line.price_gross * 5.0, 2),
        )
        com_ext = servico.find(f"{T}comExt")
        self.assertEqual(com_ext.findtext(f"{T}tpMoeda"), "220")
        self.assertEqual(
            float(com_ext.findtext(f"{T}vServMoeda")), round(self.line.price_gross, 2)
        )
        self.assertEqual(com_ext.findtext(f"{T}mdPrestacao"), "4")
        self.assertEqual(com_ext.findtext(f"{T}mecAFComexP"), "01")

    def test_taxed_service_in_dollars_is_not_an_export(self):
        """A contract in dollars in Brazil, or a customer abroad paying ISS."""
        with self._in_dollars():
            in_brazil = self._rps().find(f".//{T}Servico")
            self._abroad()
            abroad = self._rps().find(f".//{T}Servico")
        self.assertEqual(
            float(in_brazil.findtext(f"{T}Valores/{T}ValorServicos")),
            round(self.line.price_gross * 5.0, 2),
        )
        for servico in (in_brazil, abroad):
            self.assertEqual(servico.findtext(f"{T}ExigibilidadeISS"), "1")
            self.assertEqual(servico.findtext(f"{T}CodigoMunicipio"), "3518800")
            self.assertEqual(servico.findtext(f"{T}CodigoPais"), "0076")
            self.assertIsNone(servico.find(f"{T}comExt"))

    # ----------------------------------------------------------- transmission

    def test_send_authorized(self):
        self._send(RPS_NAO_ENCONTRADO, PROTOCOLO, LOTE_PROCESSADO)
        self.assertEqual(
            self.session.operacoes,
            ["ConsultarNfsePorRps", "RecepcionarLoteRps", "ConsultarLoteRps"],
        )
        self.assertEqual(
            self.session.chamadas[0]["url"],
            "https://ws-guarulhos.giss.com.br/service-ws/nf/nfse-ws",
        )
        # each RPS signed, then the lot
        lote = self.session.chamadas[1]["dados"]
        self.assertEqual(
            [r.get("URI") for r in lote.iter(f"{{{NS_DS}}}Reference")],
            ["#rps50", "#lote50"],
        )
        self.assertEqual(self.nfse.state_edoc, "autorizada")
        self.assertEqual(self.nfse.document_number, "55")
        self.assertEqual(self.nfse.verify_code, "ABC123XYZ")
        self.assertEqual(self.nfse.nfse_giss_national_key, "3" * 50)
        self.assertEqual(self.nfse.authorization_protocol, "PROT-123")
        # 10:00:05 in Brasilia is 13:00:05 UTC
        self.assertEqual(
            self.nfse.authorization_date, datetime.datetime(2026, 11, 10, 13, 0, 5)
        )
        self.assertFalse(self.nfse.edoc_error_message)

    def test_send_still_processing_then_status(self):
        self._send(RPS_NAO_ENCONTRADO, PROTOCOLO, LOTE_EM_FILA)
        self.assertEqual(self.nfse.state_edoc, "enviada")
        self.assertEqual(self.nfse.authorization_protocol, "PROT-123")
        self.assertFalse(self.nfse.document_number)
        # the status query asks for the lot by its protocol, without resending
        self.session.chamadas.clear()
        self.session.respostas = [LOTE_PROCESSADO]
        self.nfse._document_status()
        self.assertEqual(self.session.operacoes, ["ConsultarLoteRps"])
        self.assertEqual(self.nfse.state_edoc, "autorizada")
        self.assertEqual(self.nfse.document_number, "55")

    def test_send_lot_refused(self):
        self._send(RPS_NAO_ENCONTRADO, LOTE_RECUSADO)
        self.assertEqual(self.nfse.state_edoc, "rejeitada")
        self.assertIn("E160", self.nfse.edoc_error_message)
        self.assertFalse(self.nfse.authorization_protocol)

    def test_send_lot_with_error(self):
        self._send(RPS_NAO_ENCONTRADO, PROTOCOLO, LOTE_COM_ERRO)
        self.assertEqual(self.nfse.state_edoc, "rejeitada")
        self.assertIn("E174", self.nfse.edoc_error_message)
        # a rejected lot is sent again as a new lot, not queried forever
        self.assertFalse(self.nfse.authorization_protocol)

    def test_send_does_not_resend_a_rps_the_city_hall_already_has(self):
        """After a dropped connection the RPS may already be a NFS-e."""
        self._send(RPS_JA_CONVERTIDO)
        self.assertEqual(self.session.operacoes, ["ConsultarNfsePorRps"])
        self.assertEqual(self.nfse.state_edoc, "autorizada")
        self.assertEqual(self.nfse.document_number, "55")

    # ------------------------------------------------------------ cancellation

    def test_cancel(self):
        self._send(RPS_NAO_ENCONTRADO, PROTOCOLO, LOTE_PROCESSADO)
        self.session.chamadas.clear()
        self.session.respostas = [CANCELADA]
        self.nfse.nfse_giss_cancel_code = "2"
        self.nfse._document_cancel("Servico nao prestado ao cliente")
        self.assertEqual(self.session.operacoes, ["CancelarNfse"])
        pedido = self.session.chamadas[0]["dados"]
        self.assertEqual(pedido.findtext(f".//{T}Numero"), "55")
        self.assertEqual(pedido.findtext(f".//{T}CodigoCancelamento"), "2")
        self.assertEqual(self.nfse.state_edoc, "cancelada")
        self.assertTrue(self.nfse.cancel_event_id)

    def test_cancel_refused_keeps_the_document_authorized(self):
        self._send(RPS_NAO_ENCONTRADO, PROTOCOLO, LOTE_PROCESSADO)
        self.session.respostas = [CANCELAMENTO_RECUSADO]
        with self.assertRaises(UserError) as error:
            self.nfse._document_cancel("Erro na emissao da nota fiscal")
        self.assertIn("E79", str(error.exception))
        self.assertEqual(self.nfse.state_edoc, "autorizada")
