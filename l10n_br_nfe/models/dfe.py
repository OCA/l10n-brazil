# Copyright (C) 2023 KMEE Informatica LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

from datetime import datetime

from lxml import objectify
from nfelib.nfe.bindings.v4_0.leiaute_nfe_v4_00 import TnfeProc

from odoo import api, fields, models

from odoo.addons.l10n_br_fiscal_dfe.tools import utils


class DFe(models.Model):
    _inherit = "l10n_br_fiscal.dfe"

    mde_ids = fields.One2many(
        comodel_name="l10n_br_nfe.mde",
        inverse_name="dfe_id",
        string="Manifestações do Destinatário Importadas",
    )

    def _process_distribution(self, result):
        for doc in result.resposta.loteDistDFeInt.docZip:
            xml = utils.parse_gzip_xml(doc.valueOf_).read()
            root = objectify.fromstring(xml)

            mde_id = self.env["l10n_br_nfe.mde"].search(
                [
                    ("nsu", "=", utils.format_nsu(doc.NSU)),
                    ("company_id", "=", self.company_id.id),
                ],
                limit=1,
            )
            if not mde_id:
                mde_id = self._create_mde_from_schema(doc.schema, root)
                if mde_id:
                    mde_id.nsu = doc.NSU
                    mde_id.create_xml_attachment(xml)

    @api.model
    def _create_mde_from_schema(self, schema, root):
        schema_type = schema.split("_")[0]
        method = "_create_mde_from_%s" % schema_type
        if not hasattr(self, method):
            return

        return getattr(self, method)(root)

    @api.model
    def _create_mde_from_procNFe(self, root):
        nfe_key = root.protNFe.infProt.chNFe
        mde_id = self.find_mde_by_key(nfe_key)
        if mde_id:
            return mde_id

        supplier_cnpj = utils.mask_cnpj("%014d" % root.NFe.infNFe.emit.CNPJ)
        partner = self.env["res.partner"].search([("cnpj_cpf", "=", supplier_cnpj)])

        return self.env["l10n_br_nfe.mde"].create(
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

    @api.model
    def _create_mde_from_resNFe(self, root):
        nfe_key = root.chNFe
        mde_id = self.find_mde_by_key(nfe_key)
        if mde_id:
            return mde_id

        supplier_cnpj = utils.mask_cnpj("%014d" % root.CNPJ)
        partner_id = self.env["res.partner"].search([("cnpj_cpf", "=", supplier_cnpj)])

        return self.env["l10n_br_nfe.mde"].create(
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

    @api.model
    def find_mde_by_key(self, key):
        mde_id = self.env["l10n_br_nfe.mde"].search([("key", "=", key)])
        if not mde_id:
            return False

        if mde_id not in self.mde_ids:
            mde_id.dfe_id = self.id
        return mde_id

    def import_documents(self):
        for record in self:
            record.mde_ids.import_document_multi()

    @api.model
    def parse_procNFe(self, xml):
        binding = TnfeProc.from_xml(xml.read().decode())
        return self.env["l10n_br_fiscal.document"].import_binding_nfe(binding)
