# Copyright (C) 2023 KMEE Informatica LTDA
# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import base64
from datetime import datetime, timezone

from odoo import api, fields, models

from odoo.addons.l10n_br_fiscal_dfe.constants.dfe import (
    DFE_VERSION_DEFAULT,
    DFE_VERSIONS,
)
from odoo.addons.l10n_br_fiscal_dfe.tools import utils

try:
    from nfelib.nfe.bindings.v4_0.leiaute_nfe_v4_00 import TnfeProc
    from nfelib.nfe.client.v4_0.dfe import DfeClient
except ImportError:
    DfeClient = None
    TnfeProc = None

ACCESS_KEY_EXTRACTORS = {
    "procNFe": lambda root: str(root.protNFe.infProt.chNFe),
    "resNFe": lambda root: str(root.chNFe),
    "resEvento": lambda root: str(root.chNFe),
    "procEventoNFe": lambda root: str(root.evento.infEvento.chNFe),
}


class ResCompany(models.Model):
    """NF-e implementation of the generic DF-e distribution engine."""

    _inherit = "res.company"

    # ── NF-e DF-e configuration (typed fields convention) ──────────────

    nfe_dfe_version = fields.Selection(
        selection=DFE_VERSIONS,
        default=DFE_VERSION_DEFAULT,
        string="NF-e DF-e Version",
    )

    nfe_last_nsu = fields.Char(string="NF-e Last NSU", size=25, default="0")

    nfe_max_nsu = fields.Char(string="NF-e Max NSU", readonly=True)

    nfe_dfe_last_query = fields.Datetime(string="NF-e DF-e Last Query")

    nfe_dfe_last_status = fields.Char(string="NF-e DF-e Last Status", readonly=True)

    nfe_dfe_last_status_code = fields.Char(
        string="NF-e DF-e Last Status Code", readonly=True
    )

    nfe_dfe_next_query = fields.Datetime(
        string="NF-e Next Scheduled Query",
        help="NF-e DF-e distribution will not be queried before this time.",
    )

    nfe_auto_fetch = fields.Boolean(
        default=False,
        string="Auto-fetch NF-e DF-e",
        help="Periodically queries DF-e distribution for new NF-e documents",
    )

    auto_manifest_nfe = fields.Boolean(
        default=False,
        string="Automatic Recipient Manifestation (NF-e)",
        help=(
            "Automatically acknowledge receipt of notifications or events "
            "without manual intervention"
        ),
    )

    # ── Generic engine hooks ────────────────────────────────────────────

    def _dfe_get_processor(self, fiscal_type):
        if fiscal_type != "nfe":
            return super()._dfe_get_processor(fiscal_type)
        self.ensure_one()
        cert = base64.b64decode(self.certificate.file)
        return DfeClient(
            ambiente=self.nfe_environment,
            uf=self.state_id.ibge_code,
            pkcs12_data=cert,
            pkcs12_password=self.certificate.password,
            wrap_response=True,
        )

    def _dfe_extract_access_key(self, root, schema_type):
        extractor = ACCESS_KEY_EXTRACTORS.get(schema_type)
        if extractor:
            return extractor(root)
        return super()._dfe_extract_access_key(root, schema_type)

    def _dfe_cron_xmlid(self, fiscal_type):
        if fiscal_type == "nfe":
            return "l10n_br_nfe_dfe.ir_cron_search_dfe_documents"
        return super()._dfe_cron_xmlid(fiscal_type)

    def _dfe_document_action_xmlid(self, fiscal_type):
        if fiscal_type == "nfe":
            return "l10n_br_nfe_dfe.action_nfe_dfe_document"
        return super()._dfe_document_action_xmlid(fiscal_type)

    # ── NF-e specific actions ───────────────────────────────────────────

    def _nfe_dfe_document_distribution(self):
        """NF-e distribution entry point (used by cron and queue jobs)."""
        self.ensure_one()
        return self._dfe_document_distribution("nfe")

    def nfe_dfe_search_documents(self):
        for record in self:
            record._dfe_document_distribution("nfe")

    @api.model
    def _cron_nfe_dfe_search_documents(self):
        return self._cron_dfe_search_documents("nfe")

    @api.model
    def action_banner_search_all_nfe(self):
        """Called from the NF-e banner button — delegates to current company."""
        company = self.env.company
        result = company.action_document_distribution("nfe")
        return result or {"type": "ir.actions.client", "tag": "reload"}

    @api.model
    def action_banner_specific_search_nfe(self):
        """Called from the NF-e banner button — delegates to current company."""
        return self.env.company.action_search_specific("nfe")

    # ── Schema processors (NT 2014.002) ─────────────────────────────────

    def _dfe_create_from_procNFe(self, root, nsu, fiscal_type="nfe"):
        nfe_key = str(root.protNFe.infProt.chNFe)
        dfe_document = self._dfe_get_or_create_document(nfe_key, "nfe")
        supplier_cnpj = utils.mask_cnpj("%014d" % root.NFe.infNFe.emit.CNPJ)

        dfe_record = (
            self.env["l10n_br_fiscal_dfe.dfe"]
            .sudo()
            .create(
                {
                    "access_key": nfe_key,
                    "nsu": nsu,
                    "company_id": self.id,
                    "fiscal_type": "nfe",
                    "document_type_dfe": "complete",
                    "operation_type": str(root.NFe.infNFe.ide.tpNF),
                }
            )
        )

        dfe_document.sudo().dfe_ids = [(4, dfe_record.id)]
        dfe_document._update_metadata(
            {
                "emitter": str(root.NFe.infNFe.emit.xNome),
                "vat": supplier_cnpj,
                "serie": str(root.NFe.infNFe.ide.serie),
                "document_number": str(int(root.NFe.infNFe.ide.nNF)),
                "document_amount": float(root.NFe.infNFe.total.ICMSTot.vNF),
                "document_emission_date": datetime.fromisoformat(
                    str(root.NFe.infNFe.ide.dhEmi)
                )
                .astimezone(timezone.utc)
                .replace(tzinfo=None),
                "document_state": "1",
            },
            is_complete=True,
        )
        return dfe_record

    def _dfe_create_from_resNFe(self, root, nsu, fiscal_type="nfe"):
        nfe_key = str(root.chNFe)
        dfe_document = self._dfe_get_or_create_document(nfe_key, "nfe")
        supplier_cnpj = utils.mask_cnpj("%014d" % root.CNPJ)

        dfe_record = (
            self.env["l10n_br_fiscal_dfe.dfe"]
            .sudo()
            .create(
                {
                    "access_key": nfe_key,
                    "nsu": nsu,
                    "company_id": self.id,
                    "fiscal_type": "nfe",
                    "document_type_dfe": "summary",
                    "operation_type": str(root.tpNF),
                }
            )
        )

        dfe_document.sudo().dfe_ids = [(4, dfe_record.id)]
        dfe_document._update_metadata(
            {
                "emitter": str(root.xNome),
                "vat": supplier_cnpj,
                "document_amount": float(root.vNF),
                "document_emission_date": datetime.fromisoformat(str(root.dhEmi))
                .astimezone(timezone.utc)
                .replace(tzinfo=None),
                "document_state": str(root.cSitNFe),
            },
            is_complete=False,
        )

        if self.auto_manifest_nfe:
            mde = self.env["l10n_br_nfe.md_event"].create(
                {
                    "access_key": nfe_key,
                    "event_type": "ciente",
                    "company_id": self.id,
                    "document_type": "nfe",
                    "state": "draft",
                    "dfe_document_id": dfe_document.id,
                }
            )
            mde.with_delay(
                channel="root.dfe",
                description=f"Auto-manifest ciência: {nfe_key}",
            ).action_confirm()

        return dfe_record

    def _dfe_create_from_resEvento(self, root, nsu, fiscal_type="nfe"):
        nfe_key = str(root.chNFe)
        dfe_document = self._dfe_get_or_create_document(nfe_key, "nfe")

        dfe_record = (
            self.env["l10n_br_fiscal_dfe.dfe"]
            .sudo()
            .create(
                {
                    "access_key": nfe_key,
                    "nsu": nsu,
                    "company_id": self.id,
                    "fiscal_type": "nfe",
                    "document_type_dfe": "event",
                    "event_type_dfe": str(root.tpEvento),
                }
            )
        )

        dfe_document.sudo().dfe_ids = [(4, dfe_record.id)]
        return dfe_record

    def _dfe_create_from_procEventoNFe(self, root, nsu, fiscal_type="nfe"):
        nfe_key = str(root.evento.infEvento.chNFe)
        dfe_document = self._dfe_get_or_create_document(nfe_key, "nfe")

        dfe_record = (
            self.env["l10n_br_fiscal_dfe.dfe"]
            .sudo()
            .create(
                {
                    "access_key": nfe_key,
                    "nsu": nsu,
                    "company_id": self.id,
                    "fiscal_type": "nfe",
                    "document_type_dfe": "event",
                    "event_type_dfe": str(root.evento.infEvento.tpEvento),
                }
            )
        )

        dfe_document.sudo().dfe_ids = [(4, dfe_record.id)]
        return dfe_record

    # ── Import ──────────────────────────────────────────────────────────

    @api.model
    def parse_procNFe(self, xml):
        binding = TnfeProc.from_xml(xml.read().decode())
        return self.env["l10n_br_fiscal.document"].import_binding_nfe(binding)
