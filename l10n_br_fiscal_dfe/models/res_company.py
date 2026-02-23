# Copyright (C) 2023 KMEE Informatica LTDA
# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import base64
import re
from datetime import datetime, timezone

from lxml import objectify
from nfelib.nfe.bindings.v4_0.leiaute_nfe_v4_00 import TnfeProc
from nfelib.nfe.client.v4_0.dfe import DfeClient

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..constants.dfe import (
    CSTAT_CONSUMO_INDEVIDO,
    CSTAT_NO_DOCS,
    CSTAT_SUCCESS,
    DFE_ENVIRONMENT_DEFAULT,
    DFE_ENVIRONMENTS,
    DFE_INTERVAL_ERROR,
    DFE_INTERVAL_NO_DOCS,
    DFE_INTERVAL_RATE_LIMITED,
    DFE_INTERVAL_SUCCESS,
    DFE_VERSION_DEFAULT,
    DFE_VERSIONS,
)
from ..tools import utils

ACCESS_KEY_EXTRACTORS = {
    "procNFe": lambda root: str(root.protNFe.infProt.chNFe),
    "resNFe": lambda root: str(root.chNFe),
    "resEvento": lambda root: str(root.chNFe),
    "procEventoNFe": lambda root: str(root.evento.infEvento.chNFe),
}


class ResCompany(models.Model):
    _inherit = "res.company"

    # ── DF-e configuration ──────────────────────────────────────────────

    dfe_version = fields.Selection(selection=DFE_VERSIONS, default=DFE_VERSION_DEFAULT)

    dfe_environment = fields.Selection(
        selection=DFE_ENVIRONMENTS,
        default=DFE_ENVIRONMENT_DEFAULT,
    )

    last_nsu = fields.Char(string="Last NSU", size=25, default="0")

    max_nsu = fields.Char(string="Max NSU", readonly=True)

    dfe_last_query = fields.Datetime(string="Last Query")

    dfe_last_status = fields.Char(string="Last Status", readonly=True)

    dfe_last_status_code = fields.Char(string="Last Status Code", readonly=True)

    dfe_next_query = fields.Datetime(
        string="Next Scheduled Query",
        help="DF-e distribution will not be queried before this time.",
    )

    auto_fetch = fields.Boolean(
        default=False,
        string="Auto-fetch DF-e",
        help="Periodically queries DF-e distribution for new documents",
    )

    auto_manifest_nfe = fields.Boolean(
        default=False,
        string="Automatic Recipient Manifestation (NF-e)",
        help=(
            "Automatically acknowledge receipt of notifications or events "
            "without manual intervention"
        ),
    )

    # ── Helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _dfe_is_valid_nsu(nsu):
        """NSU is valid for dedup when it's a non-zero string."""
        return bool(nsu) and nsu != "000000000000000"

    def _dfe_log(self, message, log_type="info", result=None):
        """Create a distribution log entry visible in the UI.

        If a WrappedResponse ``result`` is provided, the SOAP request and
        response envelopes are stored alongside the log message.
        """
        vals = {
            "company_id": self.id,
            "log_type": log_type,
            "message": message,
        }
        if result is not None:
            if hasattr(result, "envio_xml") and result.envio_xml:
                vals["request_xml"] = (
                    result.envio_xml.decode("utf-8", errors="replace")
                    if isinstance(result.envio_xml, bytes)
                    else str(result.envio_xml)
                )
            retorno = getattr(result, "retorno", None)
            if retorno is not None:
                content = getattr(retorno, "content", None) or getattr(
                    retorno, "_content", None
                )
                if content:
                    vals["response_xml"] = (
                        content.decode("utf-8", errors="replace")
                        if isinstance(content, bytes)
                        else str(content)
                    )
        self.env["l10n_br_fiscal_dfe.distribution_log"].sudo().create(vals)

    def _dfe_schedule_next_query(self, status_code, had_exception=False):
        """Schedule the next DF-e query based on the last response status."""
        if had_exception:
            interval = DFE_INTERVAL_ERROR
        elif status_code == CSTAT_SUCCESS:
            interval = DFE_INTERVAL_SUCCESS
        elif status_code == CSTAT_NO_DOCS:
            interval = DFE_INTERVAL_NO_DOCS
        elif status_code == CSTAT_CONSUMO_INDEVIDO:
            interval = DFE_INTERVAL_RATE_LIMITED
        else:
            interval = DFE_INTERVAL_NO_DOCS
        self.sudo().dfe_next_query = fields.Datetime.now() + interval
        self._dfe_sync_cron_nextcall()

    def _dfe_sync_cron_nextcall(self):
        """Sync cron nextcall to the earliest dfe_next_query across companies."""
        cron = self.env.ref(
            "l10n_br_fiscal_dfe.ir_cron_search_dfe_documents",
            raise_if_not_found=False,
        )
        if not cron:
            return
        earliest = (
            self.env["res.company"]
            .sudo()
            .search(
                [("auto_fetch", "=", True), ("dfe_next_query", "!=", False)],
                order="dfe_next_query asc",
                limit=1,
            )
            .dfe_next_query
        )
        if earliest and earliest != cron.nextcall:
            cron.sudo().nextcall = earliest

    def _dfe_get_processor(self):
        self.ensure_one()
        cert = base64.b64decode(self.certificate.file)
        return DfeClient(
            ambiente=self.dfe_environment,
            uf=self.state_id.ibge_code,
            pkcs12_data=cert,
            pkcs12_password=self.certificate.password,
            wrap_response=True,
        )

    def _dfe_consultar_distribuicao(self, **kwargs):
        return self._dfe_get_processor().consultar_distribuicao(**kwargs)

    def _dfe_validate_distribution_response(self, result, raise_message=False):
        resp = result.resposta
        if resp.cStat == CSTAT_SUCCESS:
            return True

        code = resp.cStat
        message = getattr(resp, "xMotivo", "")

        if code == CSTAT_NO_DOCS:
            self._dfe_log(
                _(
                    "No documents found: %(code)s - %(message)s",
                    code=code,
                    message=message,
                ),
                log_type="info",
                result=result,
            )
        else:
            msg_error = _(
                "Error validating document distribution: " "\n\n%(code)s - %(message)s",
                code=code,
                message=message,
            )
            self._dfe_log(msg_error, log_type="warning", result=result)
            if raise_message:
                raise ValidationError(msg_error)
        return False

    # ── Distribution actions ────────────────────────────────────────────

    @api.model
    def action_banner_search_all(self):
        """Called from banner button — delegates to current company."""
        company = self.env.company
        result = company.action_document_distribution()
        return result or {"type": "ir.actions.client", "tag": "reload"}

    @api.model
    def action_banner_specific_search(self):
        """Called from banner button — delegates to current company."""
        return self.env.company.action_search_specific()

    def action_document_distribution(self):
        self.ensure_one()
        now = fields.Datetime.now()
        if self.dfe_next_query and self.dfe_next_query > now:
            remaining = self.dfe_next_query - now
            minutes = int(remaining.total_seconds() // 60)
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _(
                        "Cooldown active (%(code)s)",
                        code=self.dfe_last_status_code or "—",
                    ),
                    "message": _(
                        "Next query scheduled in %(minutes)s minutes.",
                        minutes=minutes,
                    ),
                    "type": "warning",
                    "sticky": False,
                },
            }
        return self._dfe_document_distribution()

    def _dfe_search_specific_document(self, access_key=None, nsu=None):
        """Search for a specific document by access key or NSU."""
        self.ensure_one()
        result = self._dfe_consultar_distribuicao(
            chave=access_key,
            nsu_especifico=utils.format_nsu(nsu) if nsu else None,
            cnpj_cpf=re.sub("[^0-9]", "", self.vat),
        )
        if not self._dfe_validate_distribution_response(result, raise_message=True):
            return
        resp = result.resposta
        self._dfe_log(
            _(
                "Specific search OK: %(cstat)s - %(motivo)s",
                cstat=resp.cStat,
                motivo=resp.xMotivo,
            ),
            log_type="success",
            result=result,
        )
        self._dfe_process_distribution(resp)

    def _dfe_document_distribution(self):
        self.ensure_one()
        last_nsu = (
            self.last_nsu
            if (self.last_nsu and self.last_nsu.isdigit())
            else "000000000000000"
        )
        raw_max = (self.max_nsu or "").strip()
        max_nsu = raw_max if (raw_max and raw_max != "000000000000000") else False
        now = fields.Datetime.now()
        if self.dfe_next_query and self.dfe_next_query > now:
            return

        last_query_time = None
        last_result = False
        Document = self.env["l10n_br_fiscal_dfe.document"].sudo()
        existing_doc_ids = set(Document.search([("company_id", "=", self.id)]).ids)
        while True:
            try:
                result = self._dfe_consultar_distribuicao(
                    cnpj_cpf=re.sub("[^0-9]", "", self.vat),
                    ultimo_nsu=utils.format_nsu(last_nsu),
                )
            except Exception as exc:
                self._dfe_log(
                    _("Error on searching documents.\n%(error)s", error=exc),
                    log_type="error",
                )
                break

            last_result = result
            last_query_time = fields.Datetime.now()
            resp = result.resposta

            if not self._dfe_validate_distribution_response(result):
                if resp.cStat == CSTAT_CONSUMO_INDEVIDO:
                    resp_nsu = getattr(resp, "ultNSU", None)
                    if resp_nsu and resp_nsu != "000000000000000":
                        last_nsu = resp_nsu
                break

            # Only update NSU from successful responses (cStat=138)
            resp_ult = getattr(resp, "ultNSU", None)
            resp_max = getattr(resp, "maxNSU", None)
            if resp_ult:
                last_nsu = resp_ult
            if resp_max:
                max_nsu = resp_max

            self._dfe_log(
                _(
                    "Distribution query OK: "
                    "%(cstat)s - %(motivo)s "
                    "(ultNSU=%(ult)s, maxNSU=%(mx)s)",
                    cstat=resp.cStat,
                    motivo=resp.xMotivo,
                    ult=last_nsu,
                    mx=max_nsu,
                ),
                log_type="success",
                result=result,
            )

            self._dfe_process_distribution(resp)

            if max_nsu and last_nsu >= max_nsu:
                break

        # Notify opted-in users about newly found documents
        current_doc_ids = set(Document.search([("company_id", "=", self.id)]).ids)
        new_doc_ids = current_doc_ids - existing_doc_ids
        if new_doc_ids:
            new_documents = Document.browse(new_doc_ids)
            self._dfe_notify_users(new_documents)

        last_resp = last_result.resposta if last_result else False
        write_vals = {
            "last_nsu": last_nsu,
            "dfe_last_query": last_query_time or self.dfe_last_query,
            "dfe_last_status": (getattr(last_resp, "xMotivo", "") if last_resp else ""),
            "dfe_last_status_code": (
                getattr(last_resp, "cStat", "") if last_resp else ""
            ),
        }
        if max_nsu:
            write_vals["max_nsu"] = max_nsu
        self.sudo().write(write_vals)
        self._dfe_schedule_next_query(
            status_code=write_vals.get("dfe_last_status_code", ""),
            had_exception=not last_result,
        )

    def _dfe_notify_users(self, new_documents):
        """Notify opted-in users about new third-party documents."""
        self.ensure_one()
        third_party_docs = new_documents.filtered(lambda d: not d.is_own_document)
        if not third_party_docs:
            return

        users = (
            self.env["res.users"]
            .sudo()
            .search(
                [
                    ("dfe_notification", "=", True),
                    ("company_ids", "in", self.id),
                ]
            )
        )
        if not users:
            return

        action = self.env.ref(
            "l10n_br_fiscal_dfe.dfe_document_action", raise_if_not_found=False
        )
        action_url = (
            f"/web#action={action.id}"
            if action
            else "/web#model=l10n_br_fiscal_dfe.document"
        )

        count = len(third_party_docs)
        company = self
        for user in users:
            self = company.with_context(lang=user.lang or "pt_BR")
            body = _(
                "<p>%(count)s new third-party DF-e document(s) found.</p>"
                '<p><a href="%(url)s">View documents</a></p>',
                count=count,
                url=action_url,
            )
            self.env["mail.thread"].sudo().message_notify(
                partner_ids=user.partner_id.ids,
                body=body,
                model="res.company",
                res_id=company.id,
            )

    def dfe_search_documents(self):
        for record in self:
            record._dfe_document_distribution()

    def action_search_specific(self):
        self.ensure_one()
        return {
            "name": _("Specific Document Search"),
            "type": "ir.actions.act_window",
            "res_model": "dfe_specific_search_wizard",
            "views": [[False, "form"]],
            "target": "new",
            "context": {"default_company_id": self.id},
        }

    # ── Cron ────────────────────────────────────────────────────────────

    @api.model
    def _cron_dfe_search_documents(self):
        now = fields.Datetime.now()
        companies = self.search(
            [
                ("auto_fetch", "=", True),
                "|",
                ("dfe_next_query", "=", False),
                ("dfe_next_query", "<=", now),
            ]
        )
        for company in companies:
            company.with_company(company).with_delay(
                description=f"NF-e: consulta distribuição DF-e ({company.name})",
            )._dfe_document_distribution()

    # ── Distribution processing ─────────────────────────────────────────

    def _dfe_process_distribution(self, result):
        DfeRecord = self.env["l10n_br_fiscal_dfe.dfe"].sudo()

        for doc in result.loteDistDFeInt.docZip:
            payload = getattr(doc, "value", None)
            if payload is None:
                payload = getattr(doc, "valueOf_", None)
            if payload is None:
                continue

            if isinstance(payload, bytes):
                b64_payload = base64.b64encode(payload).decode()
            else:
                b64_payload = payload

            xml = utils.parse_gzip_xml(b64_payload).read()
            root = objectify.fromstring(xml)

            schema = (
                getattr(doc, "schema_value", None) or getattr(doc, "schema", "") or ""
            )
            schema_type = schema.split("_")[0]

            nsu_raw = getattr(doc, "NSU", None) or getattr(doc, "nsu", None)
            nsu = utils.format_nsu(nsu_raw)

            # Dedup: if NSU is valid (non-zero), search by NSU.
            # Otherwise, search by access_key + schema_type to avoid
            # false dedup when multiple documents have NSU=0 (e.g. consChNFe).
            if self._dfe_is_valid_nsu(nsu):
                existing = DfeRecord.search(
                    [("nsu", "=", nsu), ("company_id", "=", self.id)], limit=1
                )
                if existing:
                    continue
            else:
                nsu = False
                extractor = ACCESS_KEY_EXTRACTORS.get(schema_type)
                access_key = extractor(root) if extractor else None
                if access_key:
                    existing = DfeRecord.search(
                        [
                            ("access_key", "=", access_key),
                            ("schema_type", "=", schema_type),
                            ("company_id", "=", self.id),
                        ],
                        limit=1,
                    )
                    if existing:
                        continue

            if schema_type == "procNFe":
                dfe_record = self._dfe_create_from_procNFe(root, nsu)
            elif schema_type == "resNFe":
                dfe_record = self._dfe_create_from_resNFe(root, nsu)
            elif schema_type == "resEvento":
                dfe_record = self._dfe_create_from_resEvento(root, nsu)
            elif schema_type == "procEventoNFe":
                dfe_record = self._dfe_create_from_procEventoNFe(root, nsu)
            else:
                dfe_record = DfeRecord.create(
                    {
                        "nsu": nsu,
                        "company_id": self.id,
                    }
                )
            if dfe_record:
                dfe_record.schema_type = schema_type
                dfe_record.create_xml_attachment(xml)

    def _dfe_create_from_procNFe(self, root, nsu):
        nfe_key = root.protNFe.infProt.chNFe
        dfe_document = self._dfe_get_or_create_document(nfe_key)
        supplier_cnpj = utils.mask_cnpj("%014d" % root.NFe.infNFe.emit.CNPJ)

        dfe_record = (
            self.env["l10n_br_fiscal_dfe.dfe"]
            .sudo()
            .create(
                {
                    "access_key": nfe_key,
                    "nsu": nsu,
                    "company_id": self.id,
                    "dfe_nfe_document_type": "dfe_nfe_complete",
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

    def _dfe_create_from_resNFe(self, root, nsu):
        nfe_key = root.chNFe
        dfe_document = self._dfe_get_or_create_document(nfe_key)
        supplier_cnpj = utils.mask_cnpj("%014d" % root.CNPJ)

        dfe_record = (
            self.env["l10n_br_fiscal_dfe.dfe"]
            .sudo()
            .create(
                {
                    "access_key": nfe_key,
                    "nsu": nsu,
                    "company_id": self.id,
                    "dfe_nfe_document_type": "dfe_nfe_summary",
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

    def _dfe_create_from_resEvento(self, root, nsu):
        nfe_key = root.chNFe
        dfe_document = self._dfe_get_or_create_document(nfe_key)

        dfe_record = (
            self.env["l10n_br_fiscal_dfe.dfe"]
            .sudo()
            .create(
                {
                    "access_key": nfe_key,
                    "nsu": nsu,
                    "company_id": self.id,
                    "dfe_nfe_document_type": "dfe_nfe_event",
                    "event_type_dfe": str(root.tpEvento),
                }
            )
        )

        dfe_document.sudo().dfe_ids = [(4, dfe_record.id)]
        return dfe_record

    def _dfe_create_from_procEventoNFe(self, root, nsu):
        nfe_key = root.evento.infEvento.chNFe
        dfe_document = self._dfe_get_or_create_document(nfe_key)

        dfe_record = (
            self.env["l10n_br_fiscal_dfe.dfe"]
            .sudo()
            .create(
                {
                    "access_key": nfe_key,
                    "nsu": nsu,
                    "company_id": self.id,
                    "dfe_nfe_document_type": "dfe_nfe_event",
                    "event_type_dfe": str(root.evento.infEvento.tpEvento),
                }
            )
        )

        dfe_document.sudo().dfe_ids = [(4, dfe_record.id)]
        return dfe_record

    def _dfe_get_or_create_document(self, nfe_key):
        Document = self.env["l10n_br_fiscal_dfe.document"].sudo()
        domain = [
            ("access_key", "=", nfe_key),
            ("company_id", "=", self.id),
        ]

        document = Document.search(domain, limit=1)
        if not document:
            vals = {
                "access_key": nfe_key,
                "company_id": self.id,
            }
            # Extract baseline metadata from the access key structure:
            # positions 6-20: CNPJ, 22-25: serie, 25-34: document number
            key = str(nfe_key)
            if len(key) == 44:
                cnpj_digits = key[6:20]
                vals["vat"] = utils.mask_cnpj(cnpj_digits)
                vals["serie"] = key[22:25].lstrip("0") or "0"
                vals["document_number"] = key[25:34].lstrip("0") or "0"
            document = Document.create(vals)
        return document

    @api.model
    def parse_procNFe(self, xml):
        binding = TnfeProc.from_xml(xml.read().decode())
        return self.env["l10n_br_fiscal.document"].import_binding_nfe(binding)
