# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import importlib.util
import os
from datetime import datetime
from types import SimpleNamespace
from unittest import mock

from lxml import etree

from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, TransactionCase

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    AUTORIZADO,
    CANCELADO_DENTRO_PRAZO,
    CANCELADO_FORA_PRAZO,
    DENEGADO,
    ENCERRADO,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_ENCERRADA,
    SITUACAO_EDOC_REJEITADA,
    SITUACAO_FISCAL_CANCELADO,
    SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO,
)
from odoo.addons.l10n_br_mdfe import hooks as mdfe_hooks

MDFE_NS = "http://www.portalfiscal.inf.br/mdfe"


class MDFeDocumentFlowTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("l10n_br_base.empresa_simples_nacional")
        cls.partner = cls.env.ref("l10n_br_base.res_partner_intel")
        cls.city = cls.env.ref("l10n_br_base.city_1200013")
        cls.partner.city_id = cls.city
        cls.state_ac = cls.env.ref("base.state_br_ac")
        cls.doc_type_mdfe = cls.env.ref("l10n_br_fiscal.document_58")
        cls.doc_type_nfe = cls.env.ref("l10n_br_fiscal.document_55")
        cls.doc_type_cte = cls.env.ref("l10n_br_fiscal.document_57")
        cls.serie_mdfe = cls.env["l10n_br_fiscal.document.serie"].create(
            {
                "code": "901",
                "name": "Serie 901",
                "document_type_id": cls.doc_type_mdfe.id,
                "company_id": cls.company.id,
            }
        )
        cls.serie_nfe = cls.env["l10n_br_fiscal.document.serie"].create(
            {
                "code": "902",
                "name": "Serie 902",
                "document_type_id": cls.doc_type_nfe.id,
                "company_id": cls.company.id,
            }
        )
        cls.serie_cte = cls.env["l10n_br_fiscal.document.serie"].create(
            {
                "code": "903",
                "name": "Serie 903",
                "document_type_id": cls.doc_type_cte.id,
                "company_id": cls.company.id,
            }
        )

    @classmethod
    def _create_document(cls, doc_type, serie, number):
        document = cls.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": doc_type.id,
                "company_id": cls.company.id,
                "document_number": number,
                "document_serie_id": serie.id,
                "document_serie": serie.code,
                "document_date": datetime.now(),
                "partner_id": cls.partner.id,
            }
        )
        document._generate_key()
        return document

    def setUp(self):
        super().setUp()
        self.mdfe = self._create_document(self.doc_type_mdfe, self.serie_mdfe, "90101")
        self.nfe = self._create_document(self.doc_type_nfe, self.serie_nfe, "90102")
        self.nfe.fiscal_amount_total = 100.0
        self.nfe.total_weight = 10.0

    def _fake_process(self, c_stat, x_motivo="ok", n_prot="123456789012345"):
        return SimpleNamespace(
            protocolo=SimpleNamespace(
                infProt=SimpleNamespace(
                    cStat=c_stat,
                    xMotivo=x_motivo,
                    nProt=n_prot,
                    dhRecbto=datetime.now(),
                )
            ),
            processo_xml=b"<retorno/>",
        )

    def _create_event(self, protocol_number=False):
        return self.env["l10n_br_fiscal.event"].create(
            {
                "company_id": self.company.id,
                "document_id": self.mdfe.id,
                "document_type_id": self.doc_type_mdfe.id,
                "document_serie_id": self.serie_mdfe.id,
                "document_number": self.mdfe.document_number,
                "protocol_number": protocol_number,
            }
        )

    def test_vehicle_create_and_display_name(self):
        vehicle = self.env["l10n_br_mdfe.vehicle"].create(
            {
                "name": "Caminhão",
                "partner_id": self.partner.id,
                "mdfe30_placa": "ABC1234",
                "mdfe30_cInt": "1",
            }
        )
        self.assertEqual(vehicle.display_name, "Caminhão - ABC1234 - 1")
        self.assertTrue(vehicle.active)

        vehicle_no_name = self.env["l10n_br_mdfe.vehicle"].create(
            {"partner_id": self.partner.id, "mdfe30_placa": "XYZ9876"}
        )
        self.assertEqual(vehicle_no_name.display_name, "XYZ9876")

        # "Novo Veículo" fallback: use new() since mdfe30_placa is required
        vehicle_empty = self.env["l10n_br_mdfe.vehicle"].new(
            {"partner_id": self.partner.id}
        )
        self.assertEqual(vehicle_empty.display_name, "Novo Veículo")

    def test_vehicle_default_get_partner(self):
        vehicle = (
            self.env["l10n_br_mdfe.vehicle"]
            .with_company(self.company)
            .create({"mdfe30_placa": "QWE1234"})
        )
        self.assertEqual(vehicle.partner_id, self.company.partner_id)

    def test_sync_mdfe_documents(self):
        self.mdfe.mdfe_document_ids = [Command.set([self.nfe.id])]

        descargas = self.mdfe.mdfe30_infMunDescarga
        self.assertEqual(len(descargas), 1)
        descarga = descargas[0]
        self.assertEqual(descarga.document_type, "nfe")
        self.assertEqual(descarga.city_id, self.city)
        self.assertEqual(descarga.nfe_ids.document_related_id, self.nfe)
        self.assertEqual(descarga.nfe_ids.document_key, self.nfe.document_key)
        self.assertEqual(descarga.nfe_ids.document_total_amount, 100.0)
        self.assertEqual(descarga.nfe_ids.document_total_weight, 10.0)

        # tot compute
        self.assertEqual(self.mdfe.mdfe30_qNFe, 1)
        self.assertEqual(self.mdfe.mdfe30_vCarga, 100.0)
        self.assertEqual(self.mdfe.mdfe30_qCarga, 10.0)

        # syncing again must not duplicate
        self.mdfe.mdfe_document_ids = [Command.set([self.nfe.id])]
        self.assertEqual(len(self.mdfe.mdfe30_infMunDescarga), 1)

        # removing the document removes the unloading city
        self.mdfe.mdfe_document_ids = [Command.set([])]
        self.assertFalse(
            self.mdfe.mdfe30_infMunDescarga.filtered(lambda r: r.document_type == "nfe")
        )

    def test_sync_mdfe_documents_groups_by_city(self):
        # NF-e and CT-e for the same city must share a single unloading city
        # record (infMunDescarga holds infNFe and infCTe together).
        self.cte = self._create_document(self.doc_type_cte, self.serie_cte, "90103")
        self.cte.fiscal_amount_total = 200.0
        self.cte.total_weight = 20.0
        self.mdfe.mdfe_document_ids = [Command.set([self.nfe.id, self.cte.id])]

        descargas = self.mdfe.mdfe30_infMunDescarga
        self.assertEqual(len(descargas), 1)
        descarga = descargas[0]
        self.assertEqual(descarga.city_id, self.city)
        self.assertEqual(descarga.nfe_ids.document_related_id, self.nfe)
        self.assertEqual(descarga.cte_ids.document_related_id, self.cte)
        self.assertFalse(descarga.mdfe_ids)

        # tot sums both document types
        self.assertEqual(self.mdfe.mdfe30_qNFe, 1)
        self.assertEqual(self.mdfe.mdfe30_qCTe, 1)
        self.assertEqual(self.mdfe.mdfe30_vCarga, 300.0)
        self.assertEqual(self.mdfe.mdfe30_qCarga, 30.0)

        # serialization keeps both document types in the same infMunDescarga
        inf_mdfe = self.mdfe._build_binding("mdfe", "30")
        self.assertEqual(len(inf_mdfe.infDoc.infMunDescarga), 1)
        inf_mun = inf_mdfe.infDoc.infMunDescarga[0]
        self.assertEqual(len(inf_mun.infNFe), 1)
        self.assertEqual(len(inf_mun.infCTe), 1)

    def test_sync_mdfe_documents_updates_weight_after_sync(self):
        self.mdfe.mdfe_document_ids = [Command.set([self.nfe.id])]
        self.assertEqual(self.mdfe.mdfe30_qCarga, 10.0)

        # changing the weight of the related document must be reflected in tot
        self.nfe.total_weight = 20.0
        self.assertEqual(self.mdfe.mdfe30_qCarga, 20.0)

        # a new sync keeps the related weight in sync as well
        self.nfe.total_weight = 30.0
        self.mdfe.mdfe_document_ids = [Command.set([self.nfe.id])]
        descarga = self.mdfe.mdfe30_infMunDescarga[0]
        self.assertEqual(descarga.nfe_ids.document_total_weight, 30.0)
        self.assertEqual(self.mdfe.mdfe30_qCarga, 30.0)

    def test_tot_uses_manual_weight_when_no_related_documents(self):
        # MDF-e without related documents must use the weight and amount
        # informed manually on the document itself (tot/qCarga drives the
        # "PESO TOTAL" field rendered on the DAmDFE).
        self.mdfe.total_weight = 100.0
        self.mdfe.fiscal_amount_total = 500.0
        self.assertEqual(self.mdfe.mdfe30_qCarga, 100.0)
        self.assertEqual(self.mdfe.mdfe30_vCarga, 500.0)

        # removing the last related document must fall back to the manual
        # values instead of zeroing the totals
        self.mdfe.mdfe_document_ids = [Command.set([self.nfe.id])]
        self.assertEqual(self.mdfe.mdfe30_qCarga, 10.0)
        self.mdfe.mdfe_document_ids = [Command.set([])]
        self.assertEqual(self.mdfe.mdfe30_qCarga, 100.0)
        self.assertEqual(self.mdfe.mdfe30_vCarga, 500.0)

    def test_document_number_assigns_serie(self):
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": self.doc_type_mdfe.id,
                "company_id": self.company.id,
                "issuer": "company",
                "document_number": "90201",
                "document_date": datetime.now(),
            }
        )
        document._document_number()
        self.assertTrue(document.document_serie_id)

    def test_check_mdfe_required_fields(self):
        with self.assertRaises(UserError) as cm:
            self.mdfe._document_check()
        message = str(cm.exception)
        self.assertIn("MDF-e Initial State", message)
        self.assertIn("MDF-e Unloading City", message)

    def test_check_mdfe_road_required_fields(self):
        self.mdfe.mdfe_modal = "1"
        self.mdfe.mdfe30_placa = "ABC1234"
        self.mdfe.mdfe30_tara = "7500"
        self.mdfe.mdfe30_tpRod = "03"
        self.mdfe.mdfe30_tpCar = "00"

        with self.assertRaises(UserError) as cm:
            self.mdfe._document_check()
        self.assertIn("Vehicle Driver", str(cm.exception))

        # owner equal to issuer is not allowed
        self.mdfe.mdfe30_condutor = [
            Command.create({"mdfe30_xNome": "Motorista", "mdfe30_CPF": "99999999999"})
        ]
        self.mdfe.mdfe30_prop = self.mdfe.company_id.partner_id
        with self.assertRaises(UserError) as cm:
            self.mdfe._document_check()
        self.assertIn("must be different", str(cm.exception))

        # third-party owner requires transp type
        self.mdfe.mdfe30_prop = self.partner
        with self.assertRaises(UserError) as cm:
            self.mdfe._document_check()
        self.assertIn("Transport Type must be informed", str(cm.exception))

        # transp type without owner
        self.mdfe.mdfe30_prop = False
        self.mdfe.mdfe_transp_type = "1"
        with self.assertRaises(UserError) as cm:
            self.mdfe._document_check()
        self.assertIn("Vehicle Owner is required", str(cm.exception))

        # invalid owner rntrc
        self.mdfe.mdfe30_prop = self.partner
        self.partner.rntrc_code = "12345"
        with self.assertRaises(UserError) as cm:
            self.mdfe._document_check()
        self.assertIn("RNTRC must contain exactly 8 digits", str(cm.exception))

        # complete driver data must not raise driver errors
        self.partner.rntrc_code = "12345678"
        self.mdfe.mdfe30_condutor = [
            Command.create({"mdfe30_xNome": "Motorista", "mdfe30_CPF": "99999999999"})
        ]
        missing_fields = []
        self.mdfe._check_mdfe_road_required_fields(missing_fields)
        self.assertNotIn("Driver Name", missing_fields)
        self.assertNotIn("Driver CPF", missing_fields)

    def test_action_document_closure_validation(self):
        with self.assertRaises(ValidationError):
            self.nfe.action_document_closure()

        with self.assertRaises(UserError):
            self.mdfe.action_document_closure()

        self.mdfe.state_edoc = SITUACAO_EDOC_AUTORIZADA
        action = self.mdfe.action_document_closure()
        self.assertEqual(action["res_model"], "l10n_br_fiscal.document.closure.wizard")

    def test_closure_wizard_related_cities(self):
        # Cities listed must come from the related documents (NF-e/CT-e).
        self.cte = self._create_document(self.doc_type_cte, self.serie_cte, "90103")
        self.cte.partner_id = self.env.ref("l10n_br_base.res_partner_intel")
        self.mdfe.mdfe_document_ids = [Command.set([self.nfe.id, self.cte.id])]

        wizard = (
            self.env["l10n_br_fiscal.document.closure.wizard"]
            .with_context(
                active_model="l10n_br_fiscal.document", active_id=self.mdfe.id
            )
            .create({})
        )
        self.assertIn(self.city, wizard.related_city_ids)

        # selecting a listed city fills the manual state/city fields
        listed_wizard = wizard.new({"closure_city_id": self.city.id})
        result = listed_wizard._onchange_closure_city_id()
        self.assertEqual(listed_wizard.state_id, self.city.state_id)
        self.assertEqual(listed_wizard.city_id, self.city)
        self.assertFalse(result)

        # selecting a city outside the listed ones must warn the user
        other_city = self.env["res.city"].create(
            {
                "name": "Outra Cidade",
                "state_id": self.state_ac.id,
                "country_id": self.state_ac.country_id.id,
            }
        )
        other_wizard = wizard.new({"city_id": other_city.id})
        result = other_wizard._onchange_city_id()
        self.assertTrue(result.get("warning"))
        self.assertIn("diferente da listada", result["warning"]["message"])

    def test_closure_wizard_related_cities_webclient(self):
        # The webclient flow (defaults + onchange via Form) must also load
        # the cities from the related documents into the wizard.
        self.cte = self._create_document(self.doc_type_cte, self.serie_cte, "90103")
        self.cte.partner_id = self.env.ref("l10n_br_base.res_partner_intel")
        self.mdfe.mdfe_document_ids = [Command.set([self.nfe.id, self.cte.id])]

        with Form(
            self.env["l10n_br_fiscal.document.closure.wizard"].with_context(
                active_model="l10n_br_fiscal.document", active_id=self.mdfe.id
            )
        ) as form:
            self.assertIn(self.city, form.related_city_ids)
            form.closure_city_id = self.city
            self.assertEqual(form.state_id, self.city.state_id)
            self.assertEqual(form.city_id, self.city)

    def test_document_cancel_justification(self):
        with self.assertRaises(ValidationError):
            self.mdfe._document_cancel("short")

        with mock.patch.object(type(self.mdfe), "_mdfe_cancel") as mocked:
            self.mdfe._document_cancel("justificativa valida de teste")
            mocked.assert_called_once()

    def test_get_mdfe_qrcode(self):
        with mock.patch.object(type(self.mdfe), "_edoc_processor") as mocked_processor:
            processor = mock.Mock()
            processor.monta_qrcode.return_value = "https://example.com/qrcode"
            mocked_processor.return_value = processor
            qrcode = self.mdfe.get_mdfe_qrcode()
            self.assertEqual(qrcode, "https://example.com/qrcode")
            processor.monta_qrcode.assert_called_once_with(self.mdfe.document_key)

        self.assertIsNone(self.nfe.get_mdfe_qrcode())

    def test_document_qrcode(self):
        with mock.patch.object(
            type(self.mdfe), "get_mdfe_qrcode", return_value="QRCODE"
        ):
            self.mdfe._document_qrcode()
        self.assertTrue(self.mdfe.mdfe30_infMDFeSupl)
        self.assertEqual(self.mdfe.mdfe30_infMDFeSupl.qrcode, "QRCODE")

        with mock.patch.object(
            type(self.mdfe), "get_mdfe_qrcode", return_value="QRCODE2"
        ):
            self.mdfe._document_qrcode()
        self.assertEqual(self.mdfe.mdfe30_infMDFeSupl.qrcode, "QRCODE2")

    def test_update_status_mdfe(self):
        self.mdfe.authorization_event_id = self._create_event()

        with mock.patch.object(type(self.mdfe), "_mdfe_response_add_proc"):
            self.mdfe.update_status_mdfe(self._fake_process(AUTORIZADO[0]))
        self.assertEqual(self.mdfe.state_edoc, SITUACAO_EDOC_AUTORIZADA)
        self.assertEqual(self.mdfe.status_code, AUTORIZADO[0])
        self.assertEqual(self.mdfe.authorization_event_id.state, "done")
        self.assertEqual(
            self.mdfe.authorization_event_id.protocol_number, "123456789012345"
        )

        # denied and rejected (protocol inside resposta)
        for c_stat, number, state in (
            (DENEGADO[0], "90103", SITUACAO_EDOC_DENEGADA),
            ("999", "90104", SITUACAO_EDOC_REJEITADA),
        ):
            document = self._create_document(
                self.doc_type_mdfe, self.serie_mdfe, number
            )
            process = SimpleNamespace(
                resposta=SimpleNamespace(
                    protMDFe=SimpleNamespace(
                        infProt=SimpleNamespace(
                            cStat=c_stat,
                            xMotivo="motivo",
                            nProt=False,
                            dhRecbto=datetime.now(),
                        )
                    )
                ),
                processo_xml=b"<retorno/>",
            )
            with mock.patch.object(type(document), "_mdfe_response_add_proc"):
                document.update_status_mdfe(process)
            self.assertEqual(document.state_edoc, state)
            self.assertEqual(document.status_code, c_stat)

    def test_mdfe_cancel_no_protocol(self):
        with self.assertRaises(UserError):
            self.mdfe._mdfe_cancel()

    def test_mdfe_cancel_success(self):
        self.mdfe.authorization_event_id = self._create_event(
            protocol_number="123456789012345"
        )
        self.mdfe.cancel_reason = "justificativa\ncom quebra"
        processo = SimpleNamespace(
            envio_xml=etree.Element("envEvento"),
            resposta=SimpleNamespace(
                infEvento=SimpleNamespace(
                    cStat=CANCELADO_DENTRO_PRAZO[0],
                    xMotivo="Cancelamento homologado",
                    dhRegEvento=datetime.now().isoformat(),
                    nProt="123456789012345",
                )
            ),
            retorno=SimpleNamespace(content=b"<retorno/>"),
        )
        with mock.patch.object(type(self.mdfe), "_edoc_processor") as mocked:
            processor = mock.Mock()
            processor.cancela_documento.return_value = processo
            mocked.return_value = processor
            self.mdfe._mdfe_cancel()
            processor.cancela_documento.assert_called_once_with(
                chave=self.mdfe.document_key,
                protocolo_autorizacao="123456789012345",
                justificativa="justificativa\\ncom quebra",
            )
        self.assertEqual(self.mdfe.state_edoc, SITUACAO_EDOC_CANCELADA)
        self.assertEqual(self.mdfe.state_fiscal, SITUACAO_FISCAL_CANCELADO)
        self.assertTrue(self.mdfe.cancel_event_id)

    def test_mdfe_cancel_outside_deadline(self):
        self.mdfe.authorization_event_id = self._create_event(
            protocol_number="123456789012345"
        )
        self.mdfe.cancel_reason = "justificativa fora do prazo"
        processo = SimpleNamespace(
            envio_xml=etree.Element("envEvento"),
            resposta=SimpleNamespace(
                infEvento=SimpleNamespace(
                    cStat=CANCELADO_FORA_PRAZO[0],
                    xMotivo="Cancelamento fora de prazo",
                    dhRegEvento=datetime.now().isoformat(),
                    nProt="123456789012345",
                )
            ),
            retorno=SimpleNamespace(content=b"<retorno/>"),
        )
        with mock.patch.object(type(self.mdfe), "_edoc_processor") as mocked:
            processor = mock.Mock()
            processor.cancela_documento.return_value = processo
            mocked.return_value = processor
            self.mdfe._mdfe_cancel()
        self.assertEqual(self.mdfe.state_fiscal, SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO)

    def test_mdfe_cancel_error(self):
        self.mdfe.authorization_event_id = self._create_event(
            protocol_number="123456789012345"
        )
        self.mdfe.cancel_reason = "justificativa com erro"
        processo = SimpleNamespace(
            envio_xml=etree.Element("envEvento"),
            resposta=SimpleNamespace(
                infEvento=SimpleNamespace(
                    cStat="999",
                    xMotivo="Erro",
                    dhRegEvento=datetime.now().isoformat(),
                    nProt=False,
                )
            ),
            retorno=SimpleNamespace(content=b"<retorno/>"),
        )
        with mock.patch.object(type(self.mdfe), "_edoc_processor") as mocked:
            processor = mock.Mock()
            processor.cancela_documento.return_value = processo
            mocked.return_value = processor
            with self.assertRaises(UserError):
                self.mdfe._mdfe_cancel()

    def test_document_closure_no_protocol(self):
        self.mdfe.closure_state_id = self.state_ac
        self.mdfe.closure_city_id = self.city
        with self.assertRaises(UserError):
            self.mdfe._document_closure()

    def test_document_closure_success(self):
        self.mdfe.authorization_event_id = self._create_event(
            protocol_number="123456789012345"
        )
        self.mdfe.closure_state_id = self.state_ac
        self.mdfe.closure_city_id = self.city
        processo = SimpleNamespace(
            envio_xml=etree.Element("envEvento"),
            resposta=SimpleNamespace(
                infEvento=SimpleNamespace(
                    cStat=ENCERRADO[0],
                    xMotivo="Encerramento registrado",
                    dhRegEvento=datetime.now().isoformat(),
                    nProt="123456789012345",
                )
            ),
            retorno=SimpleNamespace(content=b"<retorno/>"),
        )
        with mock.patch.object(type(self.mdfe), "_edoc_processor") as mocked:
            processor = mock.Mock()
            processor.encerra_documento.return_value = processo
            mocked.return_value = processor
            self.mdfe._document_closure()
            processor.encerra_documento.assert_called_once_with(
                chave=self.mdfe.document_key,
                protocolo_autorizacao="123456789012345",
                estado=self.state_ac.ibge_code,
                municipio=self.city.ibge_code,
            )
        self.assertEqual(self.mdfe.state_edoc, SITUACAO_EDOC_ENCERRADA)
        self.assertEqual(self.mdfe.closure_event_id.state, "done")

    def test_document_closure_error(self):
        self.mdfe.authorization_event_id = self._create_event(
            protocol_number="123456789012345"
        )
        self.mdfe.closure_state_id = self.state_ac
        self.mdfe.closure_city_id = self.city
        processo = SimpleNamespace(
            envio_xml=etree.Element("envEvento"),
            resposta=SimpleNamespace(
                infEvento=SimpleNamespace(
                    cStat="999",
                    xMotivo="Erro",
                    dhRegEvento=datetime.now().isoformat(),
                    nProt=False,
                )
            ),
            retorno=SimpleNamespace(content=b"<retorno/>"),
        )
        with mock.patch.object(type(self.mdfe), "_edoc_processor") as mocked:
            processor = mock.Mock()
            processor.encerra_documento.return_value = processo
            mocked.return_value = processor
            with self.assertRaises(UserError):
                self.mdfe._document_closure()

    def test_mdfe_create_proc_no_data(self):
        self.mdfe.send_file_id = False
        self.assertIsNone(self.mdfe._mdfe_create_proc(etree.Element("protMDFe")))

    def test_mdfe_create_proc(self):
        xml_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "mdfe",
            "v3_00",
            "leiauteMDFe",
            "MDFe35230905472475000102580200000602071611554500.xml",
        )
        with open(xml_path, "rb") as xml_file:
            attachment = self.env["ir.attachment"].create(
                {
                    "name": "enviMDFe.xml",
                    "datas": base64.b64encode(xml_file.read()),
                }
            )
        self.mdfe.send_file_id = attachment

        prot_element = etree.fromstring(
            '<mdfe:protMDFe xmlns:mdfe="%s"><mdfe:infProt/></mdfe:protMDFe>' % MDFE_NS
        )
        with mock.patch.object(type(self.mdfe), "_edoc_processor") as mocked:
            processor = mock.Mock()
            processor.monta_mdfe_proc.return_value = b"<mdfeProc/>"
            mocked.return_value = processor
            result = self.mdfe._mdfe_create_proc(prot_element)
            self.assertEqual(result, b"<mdfeProc/>")
            processor.monta_mdfe_proc.assert_called_once()

    def test_mdfe_response_add_proc_no_proc(self):
        xml_soap = (
            '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
            '<soap:Body><mdfe:protMDFe xmlns:mdfe="%s">'
            "<mdfe:infProt/></mdfe:protMDFe></soap:Body></soap:Envelope>" % MDFE_NS
        )
        process = SimpleNamespace(retorno=SimpleNamespace(content=xml_soap.encode()))
        with mock.patch.object(type(self.mdfe), "_mdfe_create_proc", return_value=None):
            self.mdfe._mdfe_response_add_proc(process)

    def test_eletronic_document_send(self):
        event = self.env["l10n_br_fiscal.event"].create(
            {
                "company_id": self.company.id,
                "document_id": self.mdfe.id,
                "document_type_id": self.doc_type_mdfe.id,
                "document_serie_id": self.serie_mdfe.id,
                "document_number": self.mdfe.document_number,
            }
        )
        self.mdfe.authorization_event_id = event
        send_file = self.env["ir.attachment"].create(
            {
                "name": "enviMDFe.xml",
                "datas": base64.b64encode(b"<enviMDFe/>"),
            }
        )
        self.mdfe.send_file_id = send_file

        authorized_process = self._fake_process(AUTORIZADO[0])

        with mock.patch.object(type(self.mdfe), "_edoc_processor") as mocked:
            processor = mock.Mock()
            processor.processar_documento.return_value = [
                SimpleNamespace(
                    webservice="mdfeRecepcao",
                    protocolo=authorized_process.protocolo,
                    resposta=SimpleNamespace(cStat="100", xMotivo="Autorizado"),
                    processo_xml=b"<retorno/>",
                )
            ]
            mocked.return_value = processor
            with mock.patch.object(type(self.mdfe), "_document_qrcode"):
                with mock.patch.object(type(self.mdfe), "_document_export"):
                    with mock.patch.object(type(self.mdfe), "_mdfe_response_add_proc"):
                        with mock.patch.object(
                            type(self.mdfe), "serialize", return_value=[object()]
                        ):
                            self.mdfe._eletronic_document_send()
        self.assertEqual(self.mdfe.state_edoc, SITUACAO_EDOC_AUTORIZADA)

    def test_closure_wizard_doit(self):
        wizard = self.env["l10n_br_fiscal.document.closure.wizard"].create(
            {
                "document_id": self.mdfe.id,
                "state_id": self.state_ac.id,
                "city_id": self.city.id,
            }
        )
        with mock.patch.object(type(self.mdfe), "_document_closure") as mocked:
            wizard.doit()
            mocked.assert_called_once()
        self.assertEqual(self.mdfe.closure_state_id, self.state_ac)
        self.assertEqual(self.mdfe.closure_city_id, self.city)

    def test_operation_action_create_new(self):
        operation = self.env.ref("l10n_br_fiscal.fo_manifesto")
        operation.document_type_ids = [
            Command.create(
                {
                    "document_type_id": self.doc_type_mdfe.id,
                    "company_id": self.company.id,
                }
            )
        ]
        result = operation.with_company(self.company).action_create_new()
        self.assertEqual(
            result["context"]["default_document_type_id"], self.doc_type_mdfe.id
        )
        serie_id = result["context"].get("default_document_serie_id")
        self.assertTrue(serie_id)
        serie = self.env["l10n_br_fiscal.document.serie"].browse(serie_id)
        self.assertEqual(serie.document_type_id, self.doc_type_mdfe)
        self.assertEqual(serie.company_id, self.company)

    def test_operation_dashboard_manifesto(self):
        operation = self.env.ref("l10n_br_fiscal.fo_manifesto")
        operation.document_type_ids = [
            Command.create(
                {
                    "document_type_id": self.doc_type_mdfe.id,
                    "company_id": self.company.id,
                }
            )
        ]
        self.mdfe.fiscal_operation_id = operation.id
        self.mdfe.state_edoc = SITUACAO_EDOC_AUTORIZADA

        dashboard = operation.get_operation_dashboard_data()
        self.assertTrue(dashboard["show_number_to_close"])
        self.assertEqual(dashboard["number_to_close"], 1)

        self.mdfe.state_edoc = SITUACAO_EDOC_ENCERRADA
        dashboard = operation.get_operation_dashboard_data()
        self.assertEqual(dashboard["number_to_close"], 0)

        sale_operation = self.env.ref("l10n_br_fiscal.fo_venda")
        sale_operation.document_type_ids = [
            Command.create(
                {
                    "document_type_id": self.doc_type_nfe.id,
                    "company_id": self.company.id,
                }
            )
        ]
        dashboard = sale_operation.get_operation_dashboard_data()
        self.assertFalse(dashboard["show_number_to_close"])
        self.assertEqual(dashboard["number_to_close"], 0)

    def test_partner_rntrc_inverse(self):
        self.partner.mdfe30_RNTRC = "12345678"
        self.assertEqual(self.partner.rntrc_code, "12345678")

        with self.assertRaises(ValidationError):
            self.partner.mdfe30_RNTRC = "1234567"

        with self.assertRaises(ValidationError):
            self.partner.mdfe30_RNTRC = "abcdefgh"

    def test_partner_binding_class(self):
        from nfelib.mdfe.bindings.v3_0 import mdfe_modal_rodoviario_v3_00 as nfelib

        prop_class = type(self.env["mdfe.30.veictracao_prop"])
        binding = self.partner._get_binding_class(prop_class)
        expected = nfelib
        for attr in prop_class._binding_type.split("."):
            expected = getattr(expected, attr)
        self.assertEqual(binding, expected)

    def test_related_partner_info(self):
        related = self.env["l10n_br_fiscal.document.related"].create(
            {
                "document_related_id": self.nfe.id,
                "document_type_id": self.doc_type_nfe.id,
                "document_key": self.nfe.document_key,
                "document_serie": "902",
                "document_number": "90102",
            }
        )
        self.assertEqual(related.partner_name, self.partner.name)
        self.assertEqual(related.partner_city_id, self.partner.city_id)

        related.document_serie = False
        related.document_number = False
        related._onchange_document_related_id()
        self.assertEqual(related.document_serie, self.nfe.document_serie)
        self.assertEqual(related.document_number, self.nfe.document_number)

    def test_descarga_onchange_document_ids(self):
        # city_id is required, so use new() to test the onchange that fills it
        descarga = self.env["l10n_br_mdfe.municipio.descarga"].new(
            {
                "document_id": self.mdfe.id,
                "document_type": "nfe",
            }
        )
        related = self.env["l10n_br_fiscal.document.related"].create(
            {
                "document_related_id": self.nfe.id,
                "document_type_id": self.doc_type_nfe.id,
                "document_key": self.nfe.document_key,
            }
        )
        descarga.nfe_ids = [Command.set([related.id])]
        descarga._onchange_document_ids()
        self.assertEqual(descarga.city_id, self.partner.city_id)

    def test_condutor_onchange_partner(self):
        condutor = self.env["l10n_br_mdfe.modal.rodoviario.veiculo.condutor"].create(
            {
                "document_id": self.mdfe.id,
                "mdfe30_xNome": "Antigo",
                "mdfe30_CPF": "11111111111",
            }
        )
        condutor.partner_id = self.partner.id
        condutor._onchange_partner_id()
        self.assertEqual(
            condutor.mdfe30_xNome, self.partner.legal_name or self.partner.name
        )
        self.assertEqual(condutor.mdfe30_CPF, self.partner.cnpj_cpf)

    @staticmethod
    def _load_pre_migrate():
        pre_migrate_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "migrations",
            "16.0.5.0.0",
            "pre-migrate.py",
        )
        spec = importlib.util.spec_from_file_location(
            "l10n_br_mdfe_pre_migrate", pre_migrate_path
        )
        pre_migrate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pre_migrate)
        return pre_migrate

    def test_pre_migrate(self):
        self._load_pre_migrate().migrate(self.env.cr, "16.0.4.2.1")

    def test_pre_migrate_with_stale_tables(self):
        pre_migrate = self._load_pre_migrate()
        cr = self.env.cr
        for table in ("mdfe_m2m_nfe_rel", "mdfe_m2m_cte_rel", "mdfe_m2m_mdfe_rel"):
            cr.execute(
                "CREATE TABLE %s (mdfe_document_id integer, related_document_id "
                "integer)" % table
            )
        pre_migrate.migrate(cr, "16.0.4.2.1")
        for table in ("mdfe_m2m_nfe_rel", "mdfe_m2m_cte_rel", "mdfe_m2m_mdfe_rel"):
            cr.execute("SELECT to_regclass('public.%s')" % table)
            self.assertIsNone(cr.fetchone()[0])

    def test_post_init_hook(self):
        module = self.env.ref("base.module_l10n_br_mdfe")
        if not module.demo:
            self.skipTest("l10n_br_mdfe is not installed with demo data")
        mdfe_hooks.post_init_hook(self.env.cr, None)
        with mock.patch.object(
            type(self.env["l10n_br_fiscal.document"]),
            "import_binding_mdfe",
            side_effect=UserError("import error"),
        ):
            mdfe_hooks.post_init_hook(self.env.cr, None)

    def test_onchange_mdfe_vehicle_id(self):
        vehicle = self.env["l10n_br_mdfe.vehicle"].create(
            {
                "partner_id": self.partner.id,
                "mdfe30_cInt": "V1",
                "mdfe30_placa": "ABC1234",
                "mdfe30_RENAVAM": "12345678901",
                "mdfe30_tara": "7500",
                "mdfe30_capKG": "15000",
                "mdfe30_capM3": "45",
                "mdfe30_tpRod": "03",
                "mdfe30_tpCar": "00",
                "rodo_vehicle_state_id": self.state_ac.id,
            }
        )
        document = self.env["l10n_br_fiscal.document"].new(
            {
                "document_type_id": self.doc_type_mdfe.id,
                "company_id": self.company.id,
            }
        )
        document.mdfe_vehicle_id = vehicle.id
        document._onchange_mdfe_vehicle_id()
        self.assertEqual(document.mdfe30_cInt, "V1")
        self.assertEqual(document.mdfe30_placa, "ABC1234")
        self.assertEqual(document.mdfe30_RENAVAM, "12345678901")
        self.assertEqual(document.mdfe30_tara, "7500")
        self.assertEqual(document.mdfe30_capKG, "15000")
        self.assertEqual(document.mdfe30_capM3, "45")
        self.assertEqual(document.mdfe30_tpRod, "03")
        self.assertEqual(document.mdfe30_tpCar, "00")
        self.assertEqual(document.rodo_vehicle_state_id, self.state_ac)

        # clearing the vehicle must not raise
        document.mdfe_vehicle_id = False
        document._onchange_mdfe_vehicle_id()

    def test_create_with_mdfe_documents(self):
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": self.doc_type_mdfe.id,
                "company_id": self.company.id,
                "issuer": "company",
                "document_date": datetime.now(),
                "mdfe_document_ids": [Command.set([self.nfe.id])],
            }
        )
        descargas = document.mdfe30_infMunDescarga
        self.assertEqual(len(descargas), 1)
        self.assertEqual(descargas.document_type, "nfe")
        self.assertEqual(descargas.nfe_ids.document_related_id, self.nfe)

    def test_default_get_mdfe(self):
        vehicle = self.env["l10n_br_mdfe.vehicle"].create(
            {
                "partner_id": self.company.partner_id.id,
                "mdfe30_placa": "DEF4321",
            }
        )
        doc_model = self.env["l10n_br_fiscal.document"].with_company(self.company)
        res = doc_model.with_context(
            default_document_type_id=self.doc_type_mdfe.id
        ).default_get(
            [
                "mdfe_initial_state_id",
                "mdfe_vehicle_id",
                "document_serie_id",
                "partner_id",
                "mdfe_loading_city_ids",
            ]
        )
        self.assertEqual(res["company_id"], self.company.id)
        self.assertEqual(res["user_id"], self.env.user.id)
        self.assertEqual(
            res["mdfe_initial_state_id"], self.company.partner_id.state_id.id
        )
        self.assertEqual(res["mdfe_vehicle_id"], vehicle.id)
        serie = self.env["l10n_br_fiscal.document.serie"].browse(
            res["document_serie_id"]
        )
        self.assertEqual(serie.document_type_id, self.doc_type_mdfe)
        self.assertEqual(serie.company_id, self.company)
        self.assertEqual(res["partner_id"], self.company.partner_id.id)
        self.assertEqual(
            res["mdfe_loading_city_ids"], [Command.set([self.company.city_id.id])]
        )

    def _create_company(self, name):
        # po_lead/security_lead are orphan NOT NULL columns left by modules
        # not installed in this DB, so provide DB defaults for the insert
        cr = self.env.cr
        for column in ("po_lead", "security_lead"):
            cr.execute("ALTER TABLE res_company ALTER COLUMN %s SET DEFAULT 0" % column)
        company = self.env["res.company"].create({"name": name})
        for column in ("po_lead", "security_lead"):
            cr.execute("ALTER TABLE res_company ALTER COLUMN %s DROP DEFAULT" % column)
        return company

    def test_generate_key_company_without_cnpj(self):
        company = self._create_company("Company Without CNPJ")
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": self.doc_type_mdfe.id,
                "company_id": company.id,
                "issuer": "company",
                "document_date": datetime.now(),
            }
        )
        with self.assertRaises(ValidationError):
            document._generate_key()

    def test_generate_key_company_without_state(self):
        company = self._create_company("Company Without State")
        company.partner_id.vat = "12.345.678/0001-95"
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": self.doc_type_mdfe.id,
                "company_id": company.id,
                "issuer": "company",
                "document_date": datetime.now(),
            }
        )
        with self.assertRaises(ValidationError):
            document._generate_key()

    def test_generate_key_without_number(self):
        # main_company has vat/state but no MDF-e serie
        company = self.env.ref("base.main_company")
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": self.doc_type_mdfe.id,
                "company_id": company.id,
                "issuer": "company",
                "document_date": datetime.now(),
            }
        )
        self.assertFalse(document.document_serie_id)
        with self.assertRaises(ValidationError):
            document._generate_key()

    def test_generate_key_number_from_serie(self):
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": self.doc_type_mdfe.id,
                "company_id": self.company.id,
                "issuer": "company",
                "document_date": datetime.now(),
            }
        )
        self.assertTrue(document.document_serie_id)
        document._generate_key()
        self.assertTrue(document.document_number)
        self.assertTrue(document.document_key)

    def test_generate_key_without_serie(self):
        company = self.env.ref("base.main_company")
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": self.doc_type_mdfe.id,
                "company_id": company.id,
                "issuer": "company",
                "document_number": "90201",
                "document_date": datetime.now(),
            }
        )
        with self.assertRaises(ValidationError):
            document._generate_key()

    def test_generate_key_serie_from_id(self):
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": self.doc_type_mdfe.id,
                "company_id": self.company.id,
                "issuer": "company",
                "document_number": "90202",
                "document_date": datetime.now(),
            }
        )
        self.env.cr.execute(
            "UPDATE l10n_br_fiscal_document SET document_serie = '' WHERE id = %s",
            (document.id,),
        )
        document.invalidate_recordset(["document_serie"])
        document._generate_key()
        self.assertEqual(document.document_serie, document.document_serie_id.code)
        self.assertTrue(document.document_key)

    def test_generate_key_without_transmission(self):
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": self.doc_type_mdfe.id,
                "company_id": self.company.id,
                "issuer": "company",
                "document_number": "90203",
                "document_date": datetime.now(),
            }
        )
        document.mdfe_transmission = False
        with self.assertRaises(ValidationError):
            document._generate_key()

    def test_generate_key_non_numeric_serie(self):
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": self.doc_type_mdfe.id,
                "company_id": self.company.id,
                "issuer": "company",
                "document_number": "90204",
                "document_date": datetime.now(),
            }
        )
        self.env.cr.execute(
            "UPDATE l10n_br_fiscal_document SET document_serie = '9A1' "
            "WHERE id = %s",
            (document.id,),
        )
        document.invalidate_recordset(["document_serie"])
        with self.assertRaises(ValidationError) as cm:
            document._generate_key()
        self.assertIn("must contain only numbers", str(cm.exception))

    def test_generate_key_number_too_long(self):
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": self.doc_type_mdfe.id,
                "company_id": self.company.id,
                "issuer": "company",
                "document_number": "9020400000",
                "document_date": datetime.now(),
            }
        )
        with self.assertRaises(ValidationError) as cm:
            document._generate_key()
        self.assertIn("must contain at most 9 numbers", str(cm.exception))

    def test_generate_key_serie_too_long(self):
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": self.doc_type_mdfe.id,
                "company_id": self.company.id,
                "issuer": "company",
                "document_number": "90206",
                "document_date": datetime.now(),
            }
        )
        self.env.cr.execute(
            "UPDATE l10n_br_fiscal_document SET document_serie = '9001' "
            "WHERE id = %s",
            (document.id,),
        )
        document.invalidate_recordset(["document_serie"])
        with self.assertRaises(ValidationError) as cm:
            document._generate_key()
        self.assertIn("must contain at most 3 numbers", str(cm.exception))

    def test_generate_key_invalid_chave_length(self):
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": self.doc_type_mdfe.id,
                "company_id": self.company.id,
                "issuer": "company",
                "document_number": "90207",
                "document_date": datetime.now(),
            }
        )
        fake_chave = mock.Mock()
        fake_chave.chave = "12345"
        fake_chave.codigo_aleatorio = "00000001"
        fake_chave.digito_verificador = "1"
        with mock.patch(
            "odoo.addons.l10n_br_mdfe.models.document.ChaveEdoc",
            return_value=fake_chave,
        ):
            with self.assertRaises(ValidationError) as cm:
                document._generate_key()
        self.assertIn("must contain exactly 44 digits", str(cm.exception))

    def test_generate_key_other_processor(self):
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": self.doc_type_mdfe.id,
                "company_id": self.company.id,
                "issuer": "company",
                "document_number": "90205",
                "document_date": datetime.now(),
            }
        )
        with mock.patch(
            "odoo.addons.l10n_br_mdfe.models.document.filtered_processador_edoc_mdfe",
            return_value=False,
        ):
            document._generate_key()
        self.assertTrue(document.document_key)

    def test_document_number_sets_serie(self):
        # main_company has vat/state but no MDF-e serie
        company = self.env.ref("base.main_company")
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "document_type_id": self.doc_type_mdfe.id,
                "company_id": company.id,
                "issuer": "company",
                "document_date": datetime.now(),
            }
        )
        self.assertFalse(document.document_serie_id)
        with mock.patch.object(
            type(self.doc_type_mdfe),
            "get_document_serie",
            return_value=self.serie_mdfe,
        ):
            document._document_number()
        self.assertEqual(document.document_serie_id, self.serie_mdfe)
        self.assertTrue(document.document_key)

    def test_check_mdfe_descarga_types(self):
        self.mdfe.mdfe30_infMunDescarga = [
            Command.create({"city_id": self.city.id, "document_type": "cte"}),
            Command.create({"city_id": self.city.id, "document_type": "mdfe"}),
        ]
        with self.assertRaises(UserError):
            self.mdfe._check_mdfe_required_fields()

    def test_validate_xml_invalid(self):
        with self.assertRaises(UserError):
            self.mdfe._validate_xml("<invalid/>")

    def test_damdfe_tot_updated_from_document(self):
        # The DAmDFE is rendered from the stored XML, which may have been
        # generated before the weight sync: the tot/qCarga must be
        # refreshed from the document so "PESO TOTAL" renders correctly.
        self.mdfe.total_weight = 100.0
        self.mdfe.fiscal_amount_total = 500.0
        self.assertEqual(self.mdfe.mdfe30_qCarga, 100.0)
        self.assertEqual(self.mdfe.mdfe30_vCarga, 500.0)

        report = self.env["ir.actions.report"]
        old_xml = (
            f'<mdfe:MDFe xmlns:mdfe="{MDFE_NS}">'
            f"<mdfe:infMDFe>"
            f"<mdfe:tot>"
            f"<mdfe:qNFe>0</mdfe:qNFe>"
            f"<mdfe:vCarga>0.00</mdfe:vCarga>"
            f"<mdfe:cUnid>01</mdfe:cUnid>"
            f"<mdfe:qCarga>0.0000</mdfe:qCarga>"
            f"</mdfe:tot>"
            f"</mdfe:infMDFe>"
            f"</mdfe:MDFe>"
        ).encode()
        updated = report._update_damdfe_tot(self.mdfe, old_xml)
        updated_root = etree.fromstring(updated)
        tot = updated_root.find(f".//{{{MDFE_NS}}}tot")
        self.assertEqual(tot.find(f"{{{MDFE_NS}}}qCarga").text, "100,00")
        self.assertEqual(tot.find(f"{{{MDFE_NS}}}vCarga").text, "500.00")
        self.assertEqual(tot.find(f"{{{MDFE_NS}}}qNFe").text, "0")

    def test_update_status_mdfe_dh_recibo_string(self):
        self.mdfe.authorization_event_id = self._create_event()
        process = self._fake_process(AUTORIZADO[0])
        process.protocolo.infProt.dhRecbto = datetime.now().isoformat()
        with mock.patch.object(type(self.mdfe), "_mdfe_response_add_proc"):
            self.mdfe.update_status_mdfe(process)
        self.assertEqual(self.mdfe.state_edoc, SITUACAO_EDOC_AUTORIZADA)
        self.assertEqual(
            self.mdfe.authorization_event_id.protocol_number, "123456789012345"
        )

    def _eletronic_document_send_setup(self):
        event = self.env["l10n_br_fiscal.event"].create(
            {
                "company_id": self.company.id,
                "document_id": self.mdfe.id,
                "document_type_id": self.doc_type_mdfe.id,
                "document_serie_id": self.serie_mdfe.id,
                "document_number": self.mdfe.document_number,
            }
        )
        self.mdfe.authorization_event_id = event
        self.mdfe.send_file_id = self.env["ir.attachment"].create(
            {
                "name": "enviMDFe.xml",
                "datas": base64.b64encode(b"<enviMDFe/>"),
            }
        )

    def test_eletronic_document_send_invalid_xml(self):
        self._eletronic_document_send_setup()
        self.mdfe.xml_error_message = "invalid xml"
        with mock.patch.object(type(self.mdfe), "_document_qrcode"):
            with mock.patch.object(type(self.mdfe), "_document_export"):
                with self.assertRaises(UserError):
                    self.mdfe._eletronic_document_send()

    def _eletronic_document_send_result(self, c_stat, expected_state):
        self._eletronic_document_send_setup()
        process = SimpleNamespace(
            webservice="consulta",
            resposta=SimpleNamespace(cStat=c_stat, xMotivo="motivo"),
        )
        with mock.patch.object(type(self.mdfe), "_document_qrcode"):
            with mock.patch.object(type(self.mdfe), "_document_export"):
                with mock.patch.object(
                    type(self.mdfe), "serialize", return_value=[object()]
                ):
                    with mock.patch.object(
                        type(self.mdfe), "_edoc_processor"
                    ) as mocked:
                        processor = mock.Mock()
                        processor.processar_documento.return_value = [process]
                        mocked.return_value = processor
                        self.mdfe._eletronic_document_send()
        self.assertEqual(self.mdfe.state_edoc, expected_state)
        self.assertEqual(self.mdfe.status_code, c_stat)

    def test_eletronic_document_send_denied(self):
        self._eletronic_document_send_result(DENEGADO[0], SITUACAO_EDOC_DENEGADA)

    def test_eletronic_document_send_rejected(self):
        self._eletronic_document_send_result("999", SITUACAO_EDOC_REJEITADA)

    def test_mdfe_response_add_proc(self):
        xml_soap = (
            '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
            '<soap:Body><mdfe:protMDFe xmlns:mdfe="%s">'
            "<mdfe:infProt/></mdfe:protMDFe></soap:Body></soap:Envelope>" % MDFE_NS
        )
        process = SimpleNamespace(retorno=SimpleNamespace(content=xml_soap.encode()))
        proc_xml = (
            '<mdfeProc xmlns="%s"><MDFe/><protMDFe/></mdfeProc>' % MDFE_NS
        ).encode()
        with mock.patch.object(
            type(self.mdfe), "_mdfe_create_proc", return_value=proc_xml
        ):
            self.mdfe._mdfe_response_add_proc(process)
        self.assertIsNotNone(process.processo)
        self.assertEqual(process.processo_xml, proc_xml)

    def test_inflotacao_local_choice(self):
        local = self.env["l10n_br_mdfe.inflotacao.local"].create({"local_type": "CEP"})
        self.assertEqual(local.mdfe30_choice_tlocal, "mdfe30_CEP")
        local.local_type = "coord"
        self.assertEqual(local.mdfe30_choice_tlocal, "mdfe30_latitude")

    def test_descarga_state_compute(self):
        descarga = self.env["l10n_br_mdfe.municipio.descarga"].create(
            {
                "document_id": self.mdfe.id,
                "city_id": self.city.id,
                "document_type": "nfe",
            }
        )
        self.assertEqual(descarga.state_id, self.state_ac)

    def test_operation_action_create_new_fallback_serie(self):
        company = self._create_company("Company No Serie 4")
        operation = self.env.ref("l10n_br_fiscal.fo_manifesto")
        operation.document_type_ids = [
            Command.create(
                {
                    "document_type_id": self.doc_type_mdfe.id,
                    "company_id": company.id,
                }
            )
        ]
        result = operation.with_company(company).action_create_new()
        self.assertEqual(
            result["context"]["default_document_type_id"], self.doc_type_mdfe.id
        )
        self.assertFalse(result["context"].get("default_document_serie_id"))

    def test_partner_rntrc_compute(self):
        self.partner.rntrc_code = "87654321"
        self.assertEqual(self.partner.mdfe30_RNTRC, "87654321")
