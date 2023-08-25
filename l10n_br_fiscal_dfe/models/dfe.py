# Copyright (C) 2023 KMEE Informatica LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import logging
import re
from datetime import datetime

from erpbrasil.assinatura import certificado as cert
from erpbrasil.transmissao import TransmissaoSOAP
from lxml import objectify
from nfelib.nfe.ws.edoc_legacy import NFeAdapter as edoc_nfe
from requests import Session

from odoo import _, api, fields, models

from ..tools import utils

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

    imported_document_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document",
        inverse_name="dfe_id",
        string="Imported Documents",
    )

    mde_ids = fields.One2many(
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

    @api.depends("company_id.name", "last_nsu")
    def name_get(self):
        return self.mapped(lambda d: (d.id, f"{d.company_id.name} - NSU: {d.last_nsu}"))

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
                    "Error validating document distribution: \n\n"
                    "%s - %s" % (code, message)
                )
            )

        return valid

    def document_distribution(self):
        maxNSU = ""
        while maxNSU != self.last_nsu:
            try:
                result = self._get_processor().consultar_distribuicao(
                    cnpj_cpf=re.sub("[^0-9]", "", self.company_id.cnpj_cpf),
                    ultimo_nsu=utils.format_nsu(self.last_nsu),
                )
            except Exception as e:
                self.message_post(body=_("Error on searching documents.\n%s" % e))
                break

            self.write(
                {
                    "last_nsu": result.resposta.ultNSU,
                    "last_query": fields.Datetime.now(),
                }
            )

            if not self.validate_distribution_response(result):
                break

            maxNSU = result.resposta.maxNSU
            for doc in result.resposta.loteDistDFeInt.docZip:
                xml = utils.parse_gzip_xml(doc.valueOf_).read()
                root = objectify.fromstring(xml)

                mde_id = self.env["l10n_br_fiscal.mde"].search(
                    [
                        ("nsu", "=", utils.format_nsu(doc.NSU)),
                        ("company_id", "=", self.company_id.id),
                    ],
                    limit=1,
                )
                if not mde_id:
                    mde_id = self.create_mde_from_schema(doc.schema, root)
                    if mde_id:
                        mde_id.nsu = doc.NSU
                        mde_id.create_xml_attachment(xml)

    def create_mde_from_schema(self, schema, root):
        schema_type = schema.split("_")[0]
        method = "create_mde_from_%s" % schema_type
        if not hasattr(self, method):
            return

        return getattr(self, method)(root)

    def create_mde_from_procNFe(self, root):
        nfe_key = root.protNFe.infProt.chNFe
        mde_id = self.find_mde_by_key(nfe_key)
        if mde_id:
            return mde_id

        supplier_cnpj = utils.mask_cnpj("%014d" % root.NFe.infNFe.emit.CNPJ)
        partner = self.env["res.partner"].search([("cnpj_cpf", "=", supplier_cnpj)])

        return self.env["l10n_br_fiscal.mde"].create(
            {
                "number": root.NFe.infNFe.ide.nNF,
                "key": nfe_key,
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
                "schema": "procNFe",
            }
        )

    def create_mde_from_resNFe(self, root):
        nfe_key = root.chNFe
        mde_id = self.find_mde_by_key(nfe_key)
        if mde_id:
            return mde_id

        supplier_cnpj = utils.mask_cnpj("%014d" % root.CNPJ)
        partner_id = self.env["res.partner"].search([("cnpj_cpf", "=", supplier_cnpj)])

        return self.env["l10n_br_fiscal.mde"].create(
            {
                "key": nfe_key,
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
                "schema": "resNFe",
            }
        )

    def find_mde_by_key(self, key):
        mde_id = self.env["l10n_br_fiscal.mde"].search([("key", "=", key)])
        if not mde_id:
            return False

        if mde_id not in self.mde_ids:
            mde_id.dfe_id = self.id
        return mde_id

    @api.model
    def parse_xml_document(self, document):
        schema_type = document.schema.split("_")[0]
        method = "parse_%s" % schema_type
        if not hasattr(self, method):
            return

        xml = utils.parse_gzip_xml(document.valueOf_)
        return getattr(self, method)(xml)

    def download_document(self, nfe_key):
        try:
            result = self._get_processor().consultar_distribuicao(
                chave=nfe_key, cnpj_cpf=re.sub("[^0-9]", "", self.company_id.cnpj_cpf)
            )
        except Exception as e:
            self.message_post(body=_("Error on searching documents.\n%s" % e))
            return

        if not self.validate_distribution_response(result):
            return

        return result.resposta.loteDistDFeInt.docZip[0]

    def import_documents(self):
        for record in self:
            record.mde_ids.import_document_multi()

    @api.model
    def _cron_search_documents(self):
        self.search([("use_cron", "=", True)]).search_documents()

    def search_documents(self):
        for record in self:
            record.document_distribution()
