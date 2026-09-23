# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import mock

from lxml import etree

from odoo.tests.common import TransactionCase, tagged

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
        cls.company.partner_id.inscr_est = False
        cls.company.partner_id.write(
            {
                "city_id": cls.goiania.id,
                "state_id": cls.goiania.state_id.id,
                "l10n_br_im_code": "778151",
            }
        )
        cls.company.write({"processador_edoc": "oca", "nfse_environment": "2"})
        doc_type = cls.env["l10n_br_fiscal.document.type"].search(
            [("code", "=", "SE")], limit=1
        )
        customer = cls.env["res.partner"].create(
            {
                "name": "Cliente NotaControl",
                "is_company": True,
                "cnpj_cpf": "44.621.819/0001-41",
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
        cnpj = "".join(c for c in self.company.cnpj_cpf if c.isdigit())
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
            "<xNome>X</xNome><end><xLgr>Y</xLgr></end><regTrib/></prest>"
            "</infDPS></DPS>"
        )
        prest = etree.fromstring(self.doc._notacontrol_adjust_dps(dps).encode()).find(
            f".//{{{NS}}}prest"
        )
        tags = [etree.QName(el).localname for el in prest]
        self.assertEqual(tags, ["CNPJ", "IM", "regTrib"])

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
        with mock.patch(
            f"{PROVIDER}.recepcionar_lote_dps_sincrono",
            return_value=retorno(
                sucesso=True,
                protocolo="P",
                chaves_acesso=["5" * 50],
                numeros_nfse=["1"],
                nfse_xml=["<Nfse/>"],
            ),
        ) as send, mock.patch(
            "odoo.addons.l10n_br_nfse_nacional.transport.adn_rest"
            ".AdnRestClient.post_dps"
        ) as adn, mock.patch(
            "odoo.addons.l10n_br_nfse_notacontrol.models.document.Certificado"
        ):
            self.company.certificate_nfe_id = self.env[
                "l10n_br_fiscal.certificate"
            ].search([], limit=1)
            self.doc._adn_send_for_authorization()
        send.assert_called_once()
        adn.assert_not_called()
        self.assertEqual(self.doc.state_edoc, "autorizada")
