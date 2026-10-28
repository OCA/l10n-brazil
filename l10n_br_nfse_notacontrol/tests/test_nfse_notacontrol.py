# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import mock

from lxml import etree
from nfelib.nfse.bindings.v1_0.dps_v1_01 import Dps

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged

from ..models.document import _SimulatedSession

NS = "http://www.sped.fazenda.gov.br/nfse"
PROVIDER = "erpbrasil.edoc.provedores.notacontrol.NotaControl"


def retorno(**kwargs):
    from erpbrasil.edoc.provedores.notacontrol import RetornoNotaControl

    values = {"operacao": "RecepcionarLoteDpsSincrono", "http_status": 200}
    values.update(xml_enviado="<x/>", xml_resposta="<y/>")
    values.update(kwargs)
    return RetornoNotaControl(**values)


@tagged("post_install", "-at_install")
class TestNfseNotaControl(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        # own records: the l10n_br_nfse_nacional demo is not required
        cls.goiania = cls.env["res.city"].search([("ibge_code", "=", "5208707")])
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        # the demo company IE is from SP: drop it before moving to GO
        cls.company.partner_id.l10n_br_ie_code = False
        cls.company.partner_id.write(
            {
                "city_id": cls.goiania.id,
                "state_id": cls.goiania.state_id.id,
                "l10n_br_im_code": "778151",
            }
        )
        cls.company.write(
            {
                "processador_edoc": "oca",
                "provedor_nfse": "nacional",
                "nfse_environment": "2",
            }
        )
        doc_type = cls.env["l10n_br_fiscal.document.type"].search(
            [("code", "=", "SE")], limit=1
        )
        customer = cls.env["res.partner"].create(
            {
                "name": "Cliente NotaControl",
                "is_company": True,
                "vat": "44.621.819/0001-41",
                "zip": "74000-000",
                "street_name": "Avenida Goias",
                "street_number": "100",
                "district": "Centro",
                "city_id": cls.goiania.id,
                "state_id": cls.goiania.state_id.id,
            }
        )
        nat_code = cls.env["l10n_br_fiscal.national.taxation.code"].create(
            {"code": "14.01.01", "name": "Manutencao de aeronaves"}
        )
        serie = cls.env["l10n_br_fiscal.document.serie"].create(
            {
                "name": "NFS-e NotaControl",
                "code": "1",
                "document_type_id": doc_type.id,
                "company_id": cls.company.id,
            }
        )
        cls.doc = cls.env["l10n_br_fiscal.document"].create(
            {
                "company_id": cls.company.id,
                "document_serie_id": serie.id,
                "partner_id": customer.id,
                "document_type_id": doc_type.id,
                "document_number": "2",
                "document_serie": "1",
                "rps_number": "0042",
                "document_key": "4" * 41,
                "fiscal_operation_type": "out",
                "processador_edoc": "oca",
                "fiscal_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Inspecao de 100 horas",
                            "national_taxation_code_id": nat_code.id,
                            "price_unit": 100.0,
                            "quantity": 1,
                            "tax_icms_or_issqn": "issqn",
                        },
                    )
                ],
            }
        )

    def setUp(self):
        super().setUp()
        # as after confirmation: the response only applies to a document
        # waiting to be sent
        self.doc.state_edoc = "a_enviar"

    def test_company_detects_notacontrol_city(self):
        self.assertTrue(self.company.nfse_notacontrol)
        other = self.env.ref("l10n_br_base.empresa_simples_nacional")
        self.assertFalse(other.nfse_notacontrol)

    def test_dps_number_and_id(self):
        """nDPS comes from the RPS number and the Id follows TSIdDPS."""
        self.assertEqual(self.doc.nfse10_nDPS, "42")
        cnpj = self.company.partner_id.cnpj_cpf_stripped
        expected = f"DPS52087072{cnpj.zfill(14)}00001{'42'.zfill(15)}"
        self.assertEqual(self.doc.nfse10_Id, expected)
        self.assertEqual(len(self.doc.nfse10_Id), 45)

    def test_codes_without_mask(self):
        line = self.doc.fiscal_line_ids[0]
        self.assertEqual(line.nfse10_cTribNac, "140101")

    def test_other_company_keeps_base_behaviour(self):
        self.company.city_id = self.env["res.city"].search(
            [("ibge_code", "=", "3550308")]
        )
        self.assertFalse(self.company.nfse_notacontrol)
        self.assertEqual(self.doc.nfse10_nDPS, self.doc.document_number)
        self.assertEqual(self.doc.nfse10_Id, f"DPS{self.doc.document_key}")

    def test_adjust_dps_removes_provider_name_and_address(self):
        dps = (
            f'<DPS xmlns="{NS}"><infDPS><prest><CNPJ>1</CNPJ><IM>2</IM>'
            "<xNome>X</xNome><end><xLgr>Y</xLgr></end>"
            "<regTrib><opSimpNac>1</opSimpNac></regTrib></prest>"
            "</infDPS></DPS>"
        )
        prest = etree.fromstring(self.doc._notacontrol_adjust_dps(dps).encode()).find(
            f".//{{{NS}}}prest"
        )
        tags = [etree.QName(el).localname for el in prest]
        self.assertEqual(tags, ["CNPJ", "IM", "regTrib"])

    def test_adjust_dps_adds_nine_digit_city_code(self):
        dps = (
            f'<DPS xmlns="{NS}"><infDPS><serv><cServ><cTribNac>140101</cTribNac>'
            "<cTribMun>140</cTribMun><xDescServ>S</xDescServ></cServ></serv>"
            "</infDPS></DPS>"
        )
        cserv = etree.fromstring(
            self.doc._notacontrol_adjust_dps(
                dps, city_taxation_code="3316301-01"
            ).encode()
        ).find(f".//{{{NS}}}cServ")
        tags = [(etree.QName(el).localname, el.text) for el in cserv]
        self.assertEqual(
            tags,
            [("cTribNac", "140101"), ("cTribMun", "331630101"), ("xDescServ", "S")],
        )

    def test_adjust_dps_to_version_101(self):
        dps = (
            f'<DPS xmlns="{NS}" versao="1.00"><infDPS><valores>'
            "<vServPrest><vServ>10.00</vServ></vServPrest><vDescCondIncond/>"
            "<trib><tribMun><tribISSQN>1</tribISSQN><pAliq>2.00</pAliq>"
            "<tpRetISSQN>1</tpRetISSQN></tribMun><tribFed><piscofins>"
            "<CST>06</CST><tpRetPisCofins>2</tpRetPisCofins></piscofins>"
            "</tribFed></trib></valores></infDPS></DPS>"
        )
        root = etree.fromstring(self.doc._notacontrol_adjust_dps(dps).encode())
        self.assertEqual(root.get("versao"), "1.01")
        self.assertIsNone(root.find(f".//{{{NS}}}vDescCondIncond"))
        self.assertEqual(root.findtext(f".//{{{NS}}}tpRetPisCofins"), "0")
        trib_mun = [
            etree.QName(el).localname for el in root.find(f".//{{{NS}}}tribMun")
        ]
        self.assertEqual(trib_mun, ["tribISSQN", "tpRetISSQN", "pAliq"])
        inf = root.find(f"{{{NS}}}infDPS")
        self.assertEqual(etree.QName(inf[-1]).localname, "IBSCBS")
        self.assertEqual(inf.findtext(f".//{{{NS}}}cClassTrib"), "000001")

    def test_adjust_dps_keeps_exported_ibscbs(self):
        dps = (
            f'<DPS xmlns="{NS}" versao="1.00"><infDPS><IBSCBS><finNFSe>0</finNFSe>'
            "<cIndOp>030101</cIndOp></IBSCBS></infDPS></DPS>"
        )
        root = etree.fromstring(self.doc._notacontrol_adjust_dps(dps).encode())
        self.assertEqual(len(root.findall(f".//{{{NS}}}IBSCBS")), 1)
        self.assertEqual(root.findtext(f".//{{{NS}}}cIndOp"), "030101")

    def test_competence_is_local_date(self):
        self.doc.document_date = "2026-09-25 01:30:00"  # UTC, 22:30 in Goiania
        self.assertEqual(self.doc.nfse10_dhEmi, "2026-09-24T22:30:00-03:00")
        self.assertEqual(self.doc.nfse10_dCompet, "2026-09-24")

    def test_rejection_read_from_soap_answer(self):
        answer = (
            '\ufeff<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">'
            f'<s:Body><RecepcionarLoteDpsSincronoResponse xmlns="{NS}">'
            "<EnviarLoteDpsSincronoResposta><ListaMensagemRetorno><MensagemRetorno>"
            "<Codigo>E160</Codigo><Mensagem>Arquivo em desacordo com o XML Schema."
            "</Mensagem></MensagemRetorno></ListaMensagemRetorno>"
            "</EnviarLoteDpsSincronoResposta></RecepcionarLoteDpsSincronoResponse>"
            "</s:Body></s:Envelope>"
        )
        self.doc._notacontrol_process_response(retorno(xml_resposta=answer))
        self.assertEqual(self.doc.status_code, "E160")
        self.assertIn("XML Schema", self.doc.edoc_error_message)

    def _city_code(self):
        return self.env["l10n_br_fiscal.city.taxation.code"].create(
            {"code": "331630101", "name": "Manutencao de aeronaves"}
        )

    def test_city_code_left_out_of_serialization(self):
        line = self.doc.fiscal_line_ids[0]
        line.city_taxation_code_id = self._city_code()
        self.assertFalse(line.nfse10_cTribMun)

    def test_serialized_dps_packed_for_notacontrol(self):
        """The real 18.0 serialization, adjusted as it is sent."""
        self.doc.document_date = "2026-10-20 13:00:00"  # set on confirmation
        self.doc.fiscal_line_ids[0].city_taxation_code_id = self._city_code()
        sent = []

        def send(dps_list, lote):
            sent.extend(dps_list)
            return retorno(mensagens=[], http_status=500)

        provider = mock.Mock(recepcionar_lote_dps_sincrono=send)
        with mock.patch.object(
            type(self.doc), "_notacontrol_provider", return_value=provider
        ):
            self.doc._adn_send_for_authorization()
        root = etree.fromstring(sent[0].encode())
        self.assertEqual(root.get("versao"), "1.01")
        inf = root.find(f"{{{NS}}}infDPS")
        self.assertEqual(inf.get("Id"), self.doc.nfse10_Id)
        self.assertEqual(inf.findtext(f"{{{NS}}}nDPS"), "42")
        cserv = [
            (etree.QName(el).localname, el.text) for el in inf.find(f".//{{{NS}}}cServ")
        ]
        self.assertEqual(cserv[:2], [("cTribNac", "140101"), ("cTribMun", "331630101")])
        prest = [etree.QName(el).localname for el in inf.find(f"{{{NS}}}prest")]
        self.assertNotIn("xNome", prest)
        self.assertNotIn("end", prest)
        self.assertIsNotNone(inf.find(f"{{{NS}}}IBSCBS"))
        # apart from Goiania's 9-digit cTribMun, the DPS is a valid national
        # DPS 1.01
        for el in inf.iter(f"{{{NS}}}cTribMun"):
            el.getparent().remove(el)
        errors = Dps.schema_validation(etree.tostring(root, encoding=str))
        self.assertEqual(errors, [])

    def test_authorized_response(self):
        self.doc._notacontrol_process_response(
            retorno(
                sucesso=True,
                protocolo="PROT-7",
                chaves_acesso=["5" * 50],
                numeros_nfse=["7"],
                nfse_xml=["<Nfse/>"],
            )
        )
        self.assertEqual(self.doc.state_edoc, "autorizada")
        self.assertEqual(self.doc.nfse_number, "7")
        self.assertEqual(self.doc.nfse_protocol, "PROT-7")

    def test_rejected_response(self):
        from erpbrasil.edoc.provedores.notacontrol import MensagemRetorno

        self.doc._notacontrol_process_response(
            retorno(mensagens=[MensagemRetorno("E160", "Schema", "Informe cTribMun")])
        )
        self.assertEqual(self.doc.state_edoc, "rejeitada")
        self.assertEqual(self.doc.status_code, "E160")
        self.assertIn("Informe cTribMun", self.doc.edoc_error_message)

    def test_send_uses_notacontrol_not_adn(self):
        with (
            mock.patch(
                f"{PROVIDER}.recepcionar_lote_dps_sincrono",
                return_value=retorno(
                    sucesso=True,
                    protocolo="P",
                    chaves_acesso=["5" * 50],
                    numeros_nfse=["1"],
                    nfse_xml=["<Nfse/>"],
                ),
            ) as send,
            mock.patch(
                "odoo.addons.l10n_br_nfse_nacional.transport.adn_rest"
                ".AdnRestClient.post_dps"
            ) as adn,
            self._mock_certificate(),
        ):
            self.doc._adn_send_for_authorization()
        send.assert_called_once()
        adn.assert_not_called()
        self.assertEqual(self.doc.state_edoc, "autorizada")

    def _mock_certificate(self):
        """No real A1 certificate in the tests: the signer is mocked."""
        return mock.patch.object(type(self.company), "_get_br_ecertificate")

    def test_provider_requires_municipal_registration(self):
        self.company.partner_id.l10n_br_im_code = False
        with self._mock_certificate(), self.assertRaises(UserError):
            self.doc._notacontrol_provider()

    def test_provider_requires_certificate(self):
        self.company.certificate_id = False
        with self.assertRaises(ValidationError):
            self.doc._notacontrol_provider()

    def test_provider_is_built_with_company_data(self):
        with (
            self._mock_certificate(),
            mock.patch(
                "odoo.addons.l10n_br_nfse_notacontrol.models.document.NotaControl"
            ) as provider,
        ):
            self.doc._notacontrol_provider(session="S")
        args, kwargs = provider.call_args
        self.assertEqual(args[2], 5208707)
        self.assertEqual(args[3], self.company.partner_id.cnpj_cpf_stripped)
        self.assertEqual(args[4], "778151")
        self.assertEqual(kwargs["algoritmo"], "sha1")
        self.assertEqual(kwargs["session"], "S")

    def test_import_keeps_dps_number(self):
        """Without the related, nDPS is mapped back to the document number."""
        vals = self.doc._prepare_import_dict({"nfse10_nDPS": "77"}, defaults_model=None)
        self.assertEqual(vals.get("document_number"), "77")
        vals = self.doc._prepare_import_dict(
            {"nfse10_nDPS": "77", "document_number": "5"}, defaults_model=None
        )
        self.assertEqual(vals.get("document_number"), "5")

    def test_dps_id_without_number_or_city(self):
        self.doc.write({"rps_number": False, "document_number": False})
        self.assertFalse(self.doc.nfse10_Id)
        self.assertFalse(self.doc.nfse10_nDPS)

    def test_simulated_session_answers_like_the_webservice(self):
        session = _SimulatedSession(self.doc)
        response = session.post("url", b"<Lote/>", {}, 10)
        body = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(session.sent, "<Lote/>")
        self.assertIn("SIMULADO", body)
        self.assertIn("<cStat>100</cStat>", body)
        self.assertIn("<nNFSe>42</nNFSe>", body)

    def test_simulated_send_authorizes_without_transmitting(self):
        self.company.nfse_notacontrol_simulated = True
        provider = mock.Mock(
            recepcionar_lote_dps_sincrono=mock.Mock(
                return_value=retorno(
                    sucesso=True,
                    protocolo="SIMULADO-1",
                    chaves_acesso=["5" * 50],
                    numeros_nfse=["42"],
                    nfse_xml=["<Nfse/>"],
                )
            )
        )
        with (
            mock.patch.object(
                type(self.doc), "_notacontrol_provider", return_value=provider
            ) as build,
            mock.patch.object(
                type(self.doc),
                "serialize",
                return_value=[mock.Mock(to_xml=lambda: "<a/>")],
            ),
        ):
            self.doc._adn_send_for_authorization()
        self.assertTrue(build.call_args.kwargs["session"])
        self.assertEqual(self.doc.state_edoc, "autorizada")
        self.assertIn("SIMULADO", self.doc.status_name)
        self.assertTrue(self.doc.message_ids.filtered(lambda m: "SIMULADO" in m.body))

    def test_other_company_send_and_cancel_use_base(self):
        self.company.city_id = self.env["res.city"].search(
            [("ibge_code", "=", "3550308")]
        )
        base = "odoo.addons.l10n_br_nfse_nacional.models.document.L10nBrFiscalDocument"
        with (
            mock.patch(f"{base}._adn_send_for_authorization") as send,
            mock.patch(f"{base}._adn_cancel", return_value=True) as cancel,
        ):
            self.doc._adn_send_for_authorization()
            self.doc._adn_cancel("Justificativa longa o bastante", "1")
        send.assert_called_once()
        cancel.assert_called_once()

    def test_simulated_cancel_is_refused(self):
        self.company.nfse_notacontrol_simulated = True
        with self.assertRaises(UserError):
            self.doc._adn_cancel("Justificativa longa o bastante", "1")

    def _cancel(self, cancel_return):
        provider = mock.Mock(cancelar_nfse=mock.Mock(return_value=cancel_return))
        with (
            mock.patch.object(
                type(self.doc), "_notacontrol_provider", return_value=provider
            ),
            mock.patch.object(
                type(self.doc), "_build_cancel_pedreg", return_value="PED"
            ),
            mock.patch.object(
                type(self.doc), "_serialize_pedreg", return_value="<ped/>"
            ),
        ):
            return self.doc._adn_cancel("Justificativa longa o bastante", "1")

    def test_cancel_records_the_event(self):
        self.assertTrue(self._cancel(retorno(sucesso=True, protocolo="C-1")))
        self.assertTrue(self.doc.cancel_event_id)
        self.assertEqual(self.doc.cancel_event_id.protocol_number, "C-1")

    def test_cancel_rejected_raises(self):
        from erpbrasil.edoc.provedores.notacontrol import MensagemRetorno

        with self.assertRaises(UserError):
            self._cancel(
                retorno(mensagens=[MensagemRetorno("E1", "Erro", "Nota ja cancelada")])
            )

    def test_rejected_without_message_uses_http_status(self):
        self.doc._notacontrol_process_response(retorno(http_status=500))
        self.assertEqual(self.doc.state_edoc, "rejeitada")
        self.assertEqual(self.doc.status_code, "500")
