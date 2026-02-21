# Copyright (C) 2023 KMEE Informatica LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import re
from datetime import datetime, timedelta

from erpbrasil.transmissao import TransmissaoSOAP
from lxml import objectify
from nfelib.nfe.bindings.v4_0.leiaute_nfe_v4_00 import TnfeProc
from nfelib.nfe.ws.edoc_legacy import NFeAdapter as edoc_nfe
from requests import Session

from odoo import _, api, fields, models

from ..tools import utils


class DFeMonitor(models.Model):
    _name = "l10n_br_fiscal.dfe_monitor"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Consult DF-e"
    _order = "id desc"
    _rec_name = "display_name"

    display_name = fields.Char(compute="_compute_display_name")

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company.id,
        readonly=True,
    )

    version = fields.Selection(related="company_id.dfe_version")

    environment = fields.Selection(related="company_id.dfe_environment")

    last_nsu = fields.Char(related="company_id.last_nsu", readonly=False)

    max_nsu = fields.Char(readonly=True)

    last_query = fields.Datetime(string="Last query")

    use_cron = fields.Boolean(
        default=False,
        string="Download new documents automatically",
        help="If activated, allows new manifestations to be automatically "
        "searched with a Cron",
    )

    automatically_acknowledge_receipt = fields.Boolean(
        default=False,
        string="Manifestar Ciência Automaticamente",
        help="Automatically acknowledge receipt"
        "of notifications or events without manual intervention",
    )  # TODO: Vê um nome melhor pro campo

    dfe_access_key_id = fields.One2many(
        comodel_name="l10n_br_fiscal.dfe_access_key",
        inverse_name="dfe_monitor_id",
        string="Chave de Acesso",
    )

    dfe_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.dfe",
        inverse_name="dfe_monitor_id",
        string="Documentos Fiscais Eletrônicos",
    )

    @api.depends("company_id.name", "last_nsu")
    def name_get(self):
        return self.mapped(lambda d: (d.id, f"{d.company_id.name} - NSU: {d.last_nsu}"))

    @api.model
    def _get_processor(self):
        certificado = self.env.company._get_br_ecertificate()
        session = Session()
        session.verify = False
        return edoc_nfe(
            TransmissaoSOAP(certificado, session),
            self.company_id.state_id.ibge_code,
            versao=self.version,
            ambiente=self.environment,
        )

    @api.model
    def validate_distribution_response(self, result):
        valid = False
        message = result.resposta.xMotivo
        if result.retorno.status_code != 200:
            code = result.retorno.status_code
        elif result.resposta.cStat != "138":
            code = result.resposta.cStat
        else:
            valid = True

        if not valid:
            self.message_post(
                body=_(
                    f"Error validating document distribution: \n\n"
                    f"{code} - {message}"
                )
            )

        return valid

    @api.model
    def _document_distribution(self):
        last_nsu = (
            self.last_nsu
            if (self.last_nsu and self.last_nsu.isdigit())
            else "000000000000000"
        )
        raw_max = (self.max_nsu or "").strip()
        maxNSU = raw_max if (raw_max and raw_max != "000000000000000") else False

        if maxNSU and last_nsu == maxNSU:
            last_query = self.last_query or fields.Datetime.now()
            if fields.Datetime.now() - last_query < timedelta(hours=1):
                self.message_post(body=_("Waiting 1 hour before making a new request."))
                return

        last_query_success = None

        while True:
            try:
                result = self._get_processor().consultar_distribuicao(
                    cnpj_cpf=re.sub("[^0-9]", "", self.company_id.vat),
                    ultimo_nsu=utils.format_nsu(last_nsu),
                )
            except Exception as e:
                self.message_post(
                    body=_("Error on searching documents.\n%(error)s", error=e)
                )
                break

            last_query_success = fields.Datetime.now()
            last_nsu = result.resposta.ultNSU
            if not maxNSU:
                maxNSU = result.resposta.maxNSU

            if not self.validate_distribution_response(result):
                break

            self._process_distribution(result)
            if last_nsu == maxNSU:
                break

        self.write(
            {
                "last_nsu": last_nsu,
                "last_query": last_query_success or self.last_query,
                "max_nsu": maxNSU,
            }
        )

    @api.model
    def _process_distribution(self, result):
        """Method to process the distribution data."""

    @api.model
    def _parse_xml_document(self, document):
        schema_type = document.schema.split("_")[0]
        method = "parse_%s" % schema_type
        if not hasattr(self, method):
            return

        xml = utils.parse_gzip_xml(document.valueOf_)
        return getattr(self, method)(xml)

    @api.model
    def _download_document(self, nfe_key):
        try:
            result = self._get_processor().consultar_distribuicao(
                chave=nfe_key, cnpj_cpf=re.sub("[^0-9]", "", self.company_id.vat)
            )
        except Exception as e:
            self.message_post(body=_("Error on searching documents.\n%s" % e))
            return

        if not self.validate_distribution_response(result):
            return

        return result.resposta.loteDistDFeInt.docZip[0]

    @api.model
    def _cron_search_documents(self):
        self.search([("use_cron", "=", True)]).search_documents()

    def search_documents(self):
        for record in self:
            record._document_distribution()

    def _process_distribution(self, result):
        for doc in result.resposta.loteDistDFeInt.docZip:
            xml = utils.parse_gzip_xml(doc.valueOf_).read()
            root = objectify.fromstring(xml)
            nsu = utils.format_nsu(doc.NSU)

            dfe_id = self.env["l10n_br_fiscal.dfe"].search(
                [
                    ("nsu", "=", nsu),
                    ("company_id", "=", self.company_id.id),
                ],
                limit=1,
            )
            if dfe_id:
                continue

            schema_type = doc.schema.split("_")[0]
            if schema_type == "procNFe":
                dfe_id = self._create_dfe_from_procNFe(root, nsu)
            elif schema_type == "resNFe":
                dfe_id = self._create_dfe_from_resNFe(root, nsu)
            elif schema_type == "resEvento":
                dfe_id = self._create_dfe_from_resEvento(root, nsu)
            elif schema_type == "procEventoNFe":
                dfe_id = self._create_dfe_from_procEventoNFe(root, nsu)
            else:
                dfe_id = self.env["l10n_br_fiscal.dfe"].create(
                    {
                        "nsu": nsu,
                        "inclusion_datetime": datetime.now(),
                        "dfe_monitor_id": self.id,
                        "company_id": self.company_id.id,
                    }
                )
            if dfe_id:
                dfe_id.create_xml_attachment(xml)
        self.dfe_access_key_id.update_manifestation_status()

    @api.model
    def _create_dfe_from_procNFe(self, root, nsu):
        nfe_key = root.protNFe.infProt.chNFe

        access_key = self._get_or_create_access_key(nfe_key)

        supplier_cnpj = utils.mask_cnpj("%014d" % root.NFe.infNFe.emit.CNPJ)
        partner = self.env["res.partner"].search([("vat", "=", supplier_cnpj)], limit=1)

        cfop_codes = []
        for det in root.NFe.infNFe.det:
            cfop_code = str(det.prod.CFOP)
            if cfop_code not in cfop_codes:
                cfop_codes.append(cfop_code)
        cfop_records = self.env["l10n_br_fiscal.cfop"].search(
            [("code", "in", cfop_codes)]
        )

        dfe = self.env["l10n_br_fiscal.dfe"].create(
            {
                "document_number": root.NFe.infNFe.ide.nNF,
                "emitter": root.NFe.infNFe.emit.xNome,
                "key": nfe_key,
                "serie": root.NFe.infNFe.ide.serie,
                "operation_type": str(root.NFe.infNFe.ide.tpNF),
                "document_amount": root.NFe.infNFe.total.ICMSTot.vNF,
                "inclusion_datetime": datetime.now(),
                "vat": supplier_cnpj,
                "ie": root.NFe.infNFe.emit.IE,
                "partner_id": partner.id,
                "emission_datetime": datetime.strptime(
                    str(root.NFe.infNFe.ide.dhEmi)[:19],
                    "%Y-%m-%dT%H:%M:%S",
                ),
                "nsu": nsu,
                "company_id": self.company_id.id,
                "inclusion_mode": "Verificação agendada",
                "dfe_monitor_id": self.id,
                "cfop_ids": [(6, 0, cfop_records.ids)],
                "dfe_nfe_document_type": "dfe_nfe_complete",
            }
        )

        access_key.dfe_ids = [(4, dfe.id)]
        return dfe

    @api.model
    def _create_dfe_from_resNFe(self, root, nsu):
        nfe_key = root.chNFe

        access_key = self._get_or_create_access_key(nfe_key)

        supplier_cnpj = utils.mask_cnpj("%014d" % root.CNPJ)
        partner_id = self.env["res.partner"].search([("vat", "=", supplier_cnpj)])

        dfe = self.env["l10n_br_fiscal.dfe"].create(
            {
                "key": nfe_key,
                "emitter": root.xNome,
                "operation_type": str(root.tpNF),
                "document_amount": root.vNF,
                "document_state": str(root.cSitNFe),
                "inclusion_datetime": datetime.now(),
                "vat": supplier_cnpj,
                "ie": root.IE,
                "partner_id": partner_id.id,
                "emission_datetime": datetime.strptime(
                    str(root.dhEmi)[:19], "%Y-%m-%dT%H:%M:%S"
                ),
                "company_id": self.company_id.id,
                "inclusion_mode": "Verificação agendada - manifestada por outro app",
                "dfe_monitor_id": self.id,
                "dfe_nfe_document_type": "dfe_nfe_summary",
                "nsu": nsu,
            }
        )

        if self.automatically_acknowledge_receipt:
            mde = self.env["l10n_br_nfe.recipient_manifestation_event"].create(
                {
                    "key": nfe_key,
                    "event_type": "ciente",
                    "event_type_selection": "ciente",
                    "company_id": self.env.company.id,
                    "dfe_access_key_id": access_key.id,
                    "mde_document_type": "mde_nfe",
                    "status": "transmitido",
                }
            )
            mde.action_confirm_selection()

        access_key.dfe_ids = [(4, dfe.id)]
        return dfe

    @api.model
    def _create_dfe_from_resEvento(self, root, nsu):
        nfe_key = root.chNFe

        access_key = self._get_or_create_access_key(nfe_key)

        supplier_cnpj = utils.mask_cnpj("%014d" % root.CNPJ)
        partner_id = self.env["res.partner"].search(
            [("vat", "=", supplier_cnpj)], limit=1
        )

        dfe = self.env["l10n_br_fiscal.dfe"].create(
            {
                "key": nfe_key,
                "inclusion_datetime": datetime.now(),
                "vat": supplier_cnpj,
                "partner_id": partner_id.id,
                "emission_datetime": datetime.strptime(
                    str(root.dhEvento)[:19], "%Y-%m-%dT%H:%M:%S"
                ),
                "company_id": self.company_id.id,
                "inclusion_mode": "Verificação agendada - manifestada por outro app",
                "dfe_monitor_id": self.id,
                "event_type_dfe": str(root.tpEvento),
                "dfe_nfe_document_type": "dfe_nfe_event",
                "nsu": nsu,
            }
        )

        access_key.dfe_ids = [(4, dfe.id)]
        return dfe

    @api.model
    def _create_dfe_from_procEventoNFe(self, root, nsu):
        nfe_key = root.evento.infEvento.chNFe

        access_key = self._get_or_create_access_key(nfe_key)

        supplier_cnpj = utils.mask_cnpj("%014d" % root.evento.infEvento.CNPJ)
        partner_id = self.env["res.partner"].search(
            [("vat", "=", supplier_cnpj)], limit=1
        )

        dfe = self.env["l10n_br_fiscal.dfe"].create(
            {
                "key": nfe_key,
                "inclusion_datetime": datetime.now(),
                "vat": supplier_cnpj,
                "partner_id": partner_id.id,
                "emission_datetime": datetime.strptime(
                    str(root.evento.infEvento.dhEvento)[:19], "%Y-%m-%dT%H:%M:%S"
                ),
                "company_id": self.company_id.id,
                "inclusion_mode": "Verificação agendada - manifestada por outro app",
                "dfe_monitor_id": self.id,
                "dfe_nfe_document_type": "dfe_nfe_event",  # TODO: tipo de DFe evento?
                "nsu": nsu,
            }
        )

        access_key.dfe_ids = [(4, dfe.id)]
        return dfe

    def _get_or_create_access_key(self, nfe_key):
        access_key = self.env["l10n_br_fiscal.dfe_access_key"].search(
            [("key", "=", nfe_key)], limit=1
        )
        if not access_key:
            access_key = self.env["l10n_br_fiscal.dfe_access_key"].create(
                {"key": nfe_key, "dfe_monitor_id": self.id}
            )
        return access_key

    @api.model
    def find_dfe_by_key(self, key):
        dfe_id = self.env["l10n_br_fiscal.dfe"].search([("key", "=", key)])
        if not dfe_id:
            return False

        if dfe_id not in self.dfe_ids:
            dfe_id.dfe_monitor_id = self.id
        return dfe_id

    def import_documents(self):
        for record in self:
            record.dfe_ids.import_document_multi()

    @api.model
    def parse_procNFe(self, xml):
        binding = TnfeProc.from_xml(xml.read().decode())
        return self.env["l10n_br_fiscal.document"].import_binding_nfe(binding)

    _sql_constraints = [
        (
            "unique_company_id",
            "unique(company_id)",
            "A DF-e Monitor already exists for this company",
        ),
    ]
