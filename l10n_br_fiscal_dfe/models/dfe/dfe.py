# Copyright (C) 2023 KMEE Informatica LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import base64
import gzip
import io
import logging
import re
from datetime import datetime

from erpbrasil.assinatura import certificado as cert
from erpbrasil.transmissao import TransmissaoSOAP
from lxml import objectify
from nfelib.nfe.bindings.v4_0.leiaute_nfe_v4_00 import TnfeProc
from nfelib.nfe.ws.edoc_legacy import NFeAdapter as edoc_nfe
from requests import Session

from odoo import _, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class DFe(models.Model):
    _name = "l10n_br_fiscal.dfe"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Consult DF-e"
    _order = "id desc"
    _rec_name = "display_name"

    display_name = fields.Char(compute="_compute_display_name")

    company_id = fields.Many2one(comodel_name="res.company", string="Company")

    version = fields.Selection(related="company_id.dfe_version")

    environment = fields.Selection(related="company_id.dfe_environment")

    last_nsu = fields.Char(string="Last NSU", size=25, default="0")

    last_query = fields.Datetime(string="Last query")

    recipient_xml_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.dfe_xml",
        inverse_name="dfe_id",
        string="XML Documents",
    )

    imported_document_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document",
        inverse_name="dfe_id",
        string="Imported Documents",
    )

    imported_mde_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.mde",
        inverse_name="dfe_id",
        string="Manifestações do Destinatário Importadas",
    )

    use_cron = fields.Boolean(
        default=False,
        string="Download new documents automatically",
        help="If activated, allows new manifestations to be automatically "
        "searched with a Cron",
    )

    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.company_id.name} - NSU: {record.last_nsu}"

    def _get_certificate(self):
        certificate_id = self.company_id.certificate_nfe_id
        return cert.Certificado(
            arquivo=certificate_id.file,
            senha=certificate_id.password,
        )

    def _get_processor(self):
        session = Session()
        session.verify = False

        return edoc_nfe(
            TransmissaoSOAP(self._get_certificate(), session),
            self.company_id.state_id.ibge_code,
            versao=self.version,
            ambiente=self.environment,
        )

    def validate_document_configuration(self):
        missing_configs = []

        if not self.company_id.certificate_nfe_id.file:
            missing_configs.append(_("Company - NF-e A1 File"))
        if not self.company_id.certificate_nfe_id.password:
            missing_configs.append(_("Company - NF-e A1 Password"))

        if missing_configs:
            raise ValidationError(
                "The following configurations are missing\n\n".join(
                    [m for m in missing_configs]
                )
            )

    def validate_distribution_response(self, result, raise_error=True):
        valid = False
        message = result.resposta.xMotivo
        if result.retorno.status_code != "200":
            code = result.retorno.status_code
        elif result.resposta.cStat not in ["137", "138"]:
            code = result.resposta.cStat
        else:
            valid = True

        if not valid:
            _logger.info(
                "Error on validating document distribution"
                " response: \n%s - %s" % (code, message)
            )
            if raise_error:
                raise ValidationError(_("%s - %s") % (code, message))

        return valid

    def read_gzip_xml(self, xml):
        arq = io.BytesIO()
        arq.write(base64.b64decode(xml))
        arq.seek(0)

        gzip_file = gzip.GzipFile(mode="r", fileobj=arq)
        return gzip_file.read()

    def document_distribution(self, raise_error):
        self.validate_document_configuration()

        try:
            result = self._get_processor().consultar_distribuicao(
                cnpj_cpf=re.sub("[^0-9]", "", self.company_id.cnpj_cpf),
                ultimo_nsu=self._format_nsu(self.last_nsu),
            )
        except Exception as e:
            _logger.error("Error on searching documents.\n%s" % e)
            if raise_error:
                raise UserError(_("Error on searching documents!\n '%s'") % e)
            return

        self.last_query = fields.Datetime.now()

        if not self.validate_distribution_response(result, raise_error):
            return

        self.env["l10n_br_fiscal.dfe_xml"].create(
            [
                {
                    "dfe_id": self.id,
                    "xml_type": "0",
                    "xml": result.envio_xml,
                },
                {
                    "dfe_id": self.id,
                    "xml_type": "1",
                    "xml": result.retorno.text,
                },
            ]
        )

        for doc in result.resposta.loteDistDFeInt.docZip:
            xml = self.read_gzip_xml(doc.valueOf_)
            root = objectify.fromstring(xml)
            self.last_nsu = doc.NSU

            mde_id = self.env["l10n_br_fiscal.mde"].search(
                [
                    ("nsu", "=", self._format_nsu(doc.NSU)),
                    ("company_id", "=", self.company_id.id),
                ],
                limit=1,
            )
            if not mde_id:
                mde_id = self.create_mde_from_schema(doc.schema, root)
                mde_id.create_xml_attachment(xml)

                self.env["l10n_br_fiscal.dfe_xml"].create(
                    {
                        "dfe_id": self.id,
                        "xml_type": "2",
                        "xml": xml,
                    }
                )

    def create_mde_from_schema(self, schema, root):
        schema_type = schema.split("_")[0]
        SCHEMA_TO_MDE_PARSER = {
            "procNFe": self.create_mde_from_procNFe,
            "resNFe": self.create_mde_from_resNFe,
        }
        return SCHEMA_TO_MDE_PARSER[schema_type](root)

    def create_mde_from_procNFe(self, root):
        supplier_cnpj = self._mask_cnpj("%014d" % root.NFe.infNFe.emit.CNPJ)
        partner = self.env["res.partner"].search([("cnpj_cpf", "=", supplier_cnpj)])

        nfe_key = root.protNFe.infProt.chNFe
        mde_id = self.find_mde_by_key(nfe_key)
        if mde_id:
            return mde_id

        return self.env["l10n_br_fiscal.mde"].create(
            {
                "number": root.NFe.infNFe.ide.nNF,
                "key": nfe_key,
                "nsu": self.last_nsu,
                "operation_type": str(root.NFe.infNFe.ide.tpNF),
                "document_value": root.NFe.infNFe.total.ICMSTot.vNF,
                "state": "pendente",
                "inclusion_datetime": datetime.now(),
                "cnpj_cpf": supplier_cnpj,
                "ie": root.NFe.infNFe.emit.IE,
                "partner_id": partner.id,
                "emission_datetime": datetime.strptime(
                    str(root.NFe.infNFe.ide.dhEmi)[:19],
                    "%Y-%m-%dT%H:%M:%S",
                ),
                "company_id": self.company_id.id,
                "dfe_id": self.id,
                "inclusion_mode": "Verificação agendada",
            }
        )

    def create_mde_from_resNFe(self, root):
        supplier_cnpj = self._mask_cnpj("%014d" % root.CNPJ)
        partner_id = self.env["res.partner"].search([("cnpj_cpf", "=", supplier_cnpj)])

        nfe_key = root.chNFe
        mde_id = self.find_mde_by_key(nfe_key)
        if mde_id:
            return mde_id

        return self.env["l10n_br_fiscal.mde"].create(
            {
                "key": nfe_key,
                "nsu": self.last_nsu,
                "emitter": root.xNome,
                "operation_type": str(root.tpNF),
                "document_value": root.vNF,
                "document_state": str(root.cSitNFe),
                "state": "pendente",
                "inclusion_datetime": datetime.now(),
                "cnpj_cpf": supplier_cnpj,
                "ie": root.IE,
                "partner_id": partner_id.id,
                "emission_datetime": datetime.strptime(
                    str(root.dhEmi)[:19], "%Y-%m-%dT%H:%M:%S"
                ),
                "company_id": self.company_id.id,
                "dfe_id": self.id,
                "inclusion_mode": "Verificação agendada - manifestada por outro app",
            }
        )

    def find_mde_by_key(self, key):
        mde_id = self.env["l10n_br_fiscal.mde"].search([("key", "=", key)])
        if not mde_id:
            return False

        if mde_id not in self.imported_mde_ids:
            mde_id.dfe_id = self.id
        return mde_id

    def parse_xml_document(self, doc_xml):
        if not doc_xml:
            return

        root = objectify.fromstring(doc_xml)
        if not hasattr(root, "NFe"):
            return

        binding = TnfeProc.from_xml(doc_xml.decode())
        document_id = (
            self.env["nfe.40.infnfe"]
            .with_context(tracking_disable=True, edoc_type="in")
            .build_from_binding(binding.NFe.infNFe)
        )
        document_id.dfe_id = self.id

        return document_id

    def download_document(self, nfe_key, raise_error=True):
        self.validate_document_configuration()

        try:
            result = self._get_processor().consultar_distribuicao(
                chave=nfe_key, cnpj_cpf=re.sub("[^0-9]", "", self.company_id.cnpj_cpf)
            )
        except Exception as e:
            _logger.error("Error on searching documents.\n%s" % e)
            if raise_error:
                raise UserError(_("Error on searching documents!\n '%s'") % e)
            return

        if not self.validate_distribution_response(result, raise_error):
            return

        return self.read_gzip_xml(result.resposta.loteDistDFeInt.docZip[0].valueOf_)

    def download_documents(self):
        document_ids = self.env["l10n_br_fiscal.document"]
        for mde_id in self.imported_mde_ids.filtered(
            lambda m: m.state in ["pendente", "ciente"]
        ):
            if mde_id.state == "pendente":
                mde_id.action_ciencia_emissao()

            xml_document = self.download_document(mde_id.key)
            document_id = self.parse_xml_document(xml_document)
            if not document_id:
                continue

            mde_id.document_id = document_id
            document_ids |= document_id

        return document_ids

    def _cron_search_documents(self):
        self.search([("use_cron", "=", True)]).search_documents(raise_error=False)

    def search_documents(self, raise_error=True):
        for record in self:
            record.document_distribution(raise_error)

    def action_manage_manifestations(self):
        return {
            "name": self.company_id.legal_name,
            "view_mode": "tree,form",
            "res_model": "l10n_br_fiscal.mde",
            "type": "ir.actions.act_window",
            "target": "current",
            "domain": [("company_id", "=", self.company_id.id)],
            "limit": self.env["l10n_br_fiscal.mde"].search_count(
                [("company_id", "=", self.company_id.id)]
            ),
        }

    @staticmethod
    def _mask_cnpj(cnpj):
        if cnpj:
            val = re.sub("[^0-9]", "", cnpj)
            if len(val) == 14:
                cnpj = "%s.%s.%s/%s-%s" % (
                    val[0:2],
                    val[2:5],
                    val[5:8],
                    val[8:12],
                    val[12:14],
                )
        return cnpj

    @staticmethod
    def _format_nsu(nsu):
        return str(nsu).zfill(15)


class DFeXML(models.Model):
    _name = "l10n_br_fiscal.dfe_xml"
    _description = "DF-e XML Document"

    dfe_id = fields.Many2one(
        string="DF-e Consult",
        comodel_name="l10n_br_fiscal.dfe",
    )

    xml_type = fields.Selection(
        selection=[
            ("0", "Envio"),
            ("1", "Resposta"),
            ("2", "Resposta-LoteDistDFeInt-DocZip(NFe)"),
        ],
        string="XML Type",
    )

    xml = fields.Char(
        string="XML",
        size=5000,
    )
