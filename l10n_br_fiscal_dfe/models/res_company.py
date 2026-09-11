# Copyright (C) 2023 KMEE Informatica LTDA
# Copyright 2026 Engenere (<https://engenere.one>).
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import base64
import re

from lxml import objectify

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..constants.dfe import (
    CSTAT_CONSUMO_INDEVIDO,
    CSTAT_NO_DOCS,
    CSTAT_SUCCESS,
    DFE_INTERVAL_ERROR,
    DFE_INTERVAL_NO_DOCS,
    DFE_INTERVAL_RATE_LIMITED,
    DFE_INTERVAL_SUCCESS,
)
from ..tools import utils


class ResCompany(models.Model):
    """Generic DF-e distribution engine.

    This module is fiscal-document agnostic: the whole distribution
    algorithm is implemented here, parameterized by ``fiscal_type``
    (e.g. "nfe", "cte"). Specific modules (l10n_br_nfe_dfe,
    l10n_br_cte_dfe...) only need to:

    - define the typed fields on res.company:
      ``{fiscal_type}_last_nsu``, ``{fiscal_type}_max_nsu``,
      ``{fiscal_type}_dfe_last_query``, ``{fiscal_type}_dfe_last_status``,
      ``{fiscal_type}_dfe_last_status_code``,
      ``{fiscal_type}_dfe_next_query``, ``{fiscal_type}_auto_fetch``
      (and ``{fiscal_type}_environment`` for the banner);
    - implement ``_dfe_get_processor(fiscal_type)`` returning a SOAP
      client exposing ``consultar_distribuicao(**kwargs)``;
    - implement ``_dfe_create_from_<schema_type>(root, nsu, fiscal_type)``
      for each schema the service distributes (procNFe, resNFe...);
    - optionaly override ``_dfe_extract_access_key``,
      ``_dfe_cron_xmlid`` and ``_dfe_document_action_xmlid``.
    """

    _inherit = "res.company"

    # ── Typed field helpers ─────────────────────────────────────────────

    @staticmethod
    def _dfe_field_name(fiscal_type, base):
        """Return the company field name for a fiscal type, e.g.
        ("nfe", "last_nsu") -> "nfe_last_nsu"."""
        return f"{fiscal_type}_{base}"

    def _dfe_get_typed_value(self, fiscal_type, base, default=False):
        return getattr(self, self._dfe_field_name(fiscal_type, base), default)

    def _dfe_write_typed(self, fiscal_type, vals):
        """Write {base: value} dict into the typed company fields."""
        self.sudo().write(
            {self._dfe_field_name(fiscal_type, k): v for k, v in vals.items()}
        )

    # ── Hooks to implement in fiscal type specific modules ──────────────

    def _dfe_get_processor(self, fiscal_type):
        """Return the SOAP client for the given fiscal type."""
        raise NotImplementedError(
            "_dfe_get_processor() must be implemented in fiscal type specific "
            "modules (e.g., l10n_br_nfe_dfe, l10n_br_cte_dfe)."
        )

    def _dfe_consultar_distribuicao(self, fiscal_type, **kwargs):
        return self._dfe_get_processor(fiscal_type).consultar_distribuicao(**kwargs)

    def _dfe_extract_access_key(self, root, schema_type):
        """Extract the access key from a parsed DF-e payload.

        Used for the dedup fallback when the NSU is zero (consChNFe in
        homologation). Should be overridden by specific modules.
        """
        return None

    def _dfe_cron_xmlid(self, fiscal_type):
        """XML id of the ir.cron to sync nextcall with, per fiscal type."""
        return None

    def _dfe_document_action_xmlid(self, fiscal_type):
        """XML id of the act_window opening the document list, per type."""
        return "l10n_br_fiscal_dfe.dfe_document_action"

    # ── Helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _dfe_is_valid_nsu(nsu):
        """NSU is valid for dedup when it's a non-zero string."""
        return bool(nsu) and nsu != "000000000000000"

    def _dfe_log(self, message, log_type="info", result=None, fiscal_type=False):
        """Create a distribution log entry visible in the UI.

        If a WrappedResponse ``result`` is provided, the SOAP request and
        response envelopes are stored alongside the log message.
        """
        vals = {
            "company_id": self.id,
            "log_type": log_type,
            "message": message,
            "fiscal_type": fiscal_type,
        }
        if result is not None:
            if getattr(result, "envio_xml", False):
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

    def _dfe_schedule_next_query(self, status_code, fiscal_type, had_exception=False):
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
        self._dfe_write_typed(
            fiscal_type, {"dfe_next_query": fields.Datetime.now() + interval}
        )
        self._dfe_sync_cron_nextcall(fiscal_type)

    def _dfe_sync_cron_nextcall(self, fiscal_type):
        """Sync cron nextcall to the earliest typed dfe_next_query."""
        cron_xmlid = self._dfe_cron_xmlid(fiscal_type)  # pylint: disable=assignment-from-none
        if not cron_xmlid:
            return
        cron = self.env.ref(cron_xmlid, raise_if_not_found=False)
        if not cron:
            return
        auto_fetch_field = self._dfe_field_name(fiscal_type, "auto_fetch")
        next_query_field = self._dfe_field_name(fiscal_type, "dfe_next_query")
        earliest = (
            self.env["res.company"]
            .sudo()
            .search(
                [(auto_fetch_field, "=", True), (next_query_field, "!=", False)],
                order=f"{next_query_field} asc",
                limit=1,
            )[next_query_field]
        )
        if earliest and earliest != cron.nextcall:
            cron.sudo().nextcall = earliest

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
                "Error validating document distribution: \n\n%(code)s - %(message)s",
                code=code,
                message=message,
            )
            self._dfe_log(msg_error, log_type="warning", result=result)
            if raise_message:
                raise ValidationError(msg_error)
        return False

    # ── Distribution actions ────────────────────────────────────────────

    def action_document_distribution(self, fiscal_type):
        self.ensure_one()
        now = fields.Datetime.now()
        next_query = self._dfe_get_typed_value(fiscal_type, "dfe_next_query")
        if next_query and next_query > now:
            remaining = next_query - now
            minutes = int(remaining.total_seconds() // 60)
            status_code = self._dfe_get_typed_value(fiscal_type, "dfe_last_status_code")
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _(
                        "Cooldown active (%(code)s)",
                        code=status_code or "—",
                    ),
                    "message": _(
                        "Next query scheduled in %(minutes)s minutes.",
                        minutes=minutes,
                    ),
                    "type": "warning",
                    "sticky": False,
                },
            }
        return self._dfe_document_distribution(fiscal_type)

    def _dfe_search_specific_document(self, fiscal_type, access_key=None, nsu=None):
        """Search for a specific document by access key or NSU."""
        self.ensure_one()
        result = self._dfe_consultar_distribuicao(
            fiscal_type,
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
            fiscal_type=fiscal_type,
        )
        self._dfe_process_distribution(resp, fiscal_type)

    def _dfe_document_distribution(self, fiscal_type):
        self.ensure_one()
        last_nsu = str(self._dfe_get_typed_value(fiscal_type, "last_nsu") or "0")
        last_nsu = last_nsu if last_nsu.isdigit() else "000000000000000"
        raw_max = str(self._dfe_get_typed_value(fiscal_type, "max_nsu") or "").strip()
        max_nsu = raw_max if (raw_max and raw_max != "000000000000000") else False
        now = fields.Datetime.now()
        next_query = self._dfe_get_typed_value(fiscal_type, "dfe_next_query")
        if next_query and next_query > now:
            return

        last_query_time = None
        last_result = False
        Document = self.env["l10n_br_fiscal_dfe.document"].sudo()
        existing_doc_ids = set(
            Document.search(
                [("company_id", "=", self.id), ("fiscal_type", "=", fiscal_type)]
            ).ids
        )
        while True:
            try:
                result = self._dfe_consultar_distribuicao(
                    fiscal_type,
                    cnpj_cpf=re.sub("[^0-9]", "", self.vat),
                    ultimo_nsu=utils.format_nsu(last_nsu),
                )
            except Exception as exc:
                self._dfe_log(
                    _("Error on searching documents.\n%(error)s", error=exc),
                    log_type="error",
                    fiscal_type=fiscal_type,
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
                fiscal_type=fiscal_type,
            )

            self._dfe_process_distribution(resp, fiscal_type)

            if max_nsu and last_nsu >= max_nsu:
                break

        # Notify opted-in users about newly found documents
        current_doc_ids = set(
            Document.search(
                [("company_id", "=", self.id), ("fiscal_type", "=", fiscal_type)]
            ).ids
        )
        new_doc_ids = current_doc_ids - existing_doc_ids
        if new_doc_ids:
            new_documents = Document.browse(new_doc_ids)
            self._dfe_notify_users(new_documents, fiscal_type)

        last_resp = last_result.resposta if last_result else False
        write_vals = {
            "last_nsu": last_nsu,
            "dfe_last_query": last_query_time
            or self._dfe_get_typed_value(fiscal_type, "dfe_last_query"),
            "dfe_last_status": (getattr(last_resp, "xMotivo", "") if last_resp else ""),
            "dfe_last_status_code": (
                getattr(last_resp, "cStat", "") if last_resp else ""
            ),
        }
        if max_nsu:
            write_vals["max_nsu"] = max_nsu
        self._dfe_write_typed(fiscal_type, write_vals)
        self._dfe_schedule_next_query(
            status_code=write_vals.get("dfe_last_status_code", ""),
            fiscal_type=fiscal_type,
            had_exception=not last_result,
        )

    def _dfe_notify_users(self, new_documents, fiscal_type):
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

        action_xmlid = self._dfe_document_action_xmlid(fiscal_type)
        action = self.env.ref(action_xmlid, raise_if_not_found=False)
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

    def dfe_search_documents(self, fiscal_type):
        for record in self:
            record._dfe_document_distribution(fiscal_type)

    def action_search_specific(self, fiscal_type):
        self.ensure_one()
        return {
            "name": _("Specific Document Search"),
            "type": "ir.actions.act_window",
            "res_model": "dfe.specific.search.wizard",
            "views": [[False, "form"]],
            "target": "new",
            "context": {
                "default_company_id": self.id,
                "default_fiscal_type": fiscal_type,
            },
        }

    # ── Cron ────────────────────────────────────────────────────────────

    @api.model
    def _cron_dfe_search_documents(self, fiscal_type):
        now = fields.Datetime.now()
        auto_fetch_field = self._dfe_field_name(fiscal_type, "auto_fetch")
        next_query_field = self._dfe_field_name(fiscal_type, "dfe_next_query")
        companies = self.search(
            [
                (auto_fetch_field, "=", True),
                "|",
                (next_query_field, "=", False),
                (next_query_field, "<=", now),
            ]
        )
        for company in companies:
            company.with_company(company).with_delay(
                description=(
                    f"DF-e ({fiscal_type}): distribution query ({company.name})"
                ),
            )._dfe_document_distribution(fiscal_type)

    # ── Distribution processing ─────────────────────────────────────────

    def _dfe_process_distribution(self, result, fiscal_type):
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
                    [
                        ("nsu", "=", nsu),
                        ("company_id", "=", self.id),
                        ("fiscal_type", "=", fiscal_type),
                    ],
                    limit=1,
                )
                if existing:
                    continue
            else:
                nsu = False
                access_key = self._dfe_extract_access_key(  # pylint: disable=assignment-from-none
                    root, schema_type
                )
                if access_key:
                    existing = DfeRecord.search(
                        [
                            ("access_key", "=", access_key),
                            ("schema_type", "=", schema_type),
                            ("company_id", "=", self.id),
                            ("fiscal_type", "=", fiscal_type),
                        ],
                        limit=1,
                    )
                    if existing:
                        continue

            create_method = getattr(self, f"_dfe_create_from_{schema_type}", None)
            if create_method:
                dfe_record = create_method(root, nsu, fiscal_type)
            else:
                dfe_record = DfeRecord.create(
                    {
                        "nsu": nsu,
                        "company_id": self.id,
                        "fiscal_type": fiscal_type,
                    }
                )
            if dfe_record:
                dfe_record.schema_type = schema_type
                dfe_record.create_xml_attachment(xml)

    def _dfe_get_or_create_document(self, access_key, fiscal_type):
        Document = self.env["l10n_br_fiscal_dfe.document"].sudo()
        domain = [
            ("access_key", "=", access_key),
            ("company_id", "=", self.id),
        ]

        document = Document.search(domain, limit=1)
        if not document:
            vals = {
                "access_key": access_key,
                "company_id": self.id,
                "fiscal_type": fiscal_type,
            }
            # Extract baseline metadata from the access key structure:
            # positions 6-20: CNPJ, 22-25: serie, 25-34: document number
            key = str(access_key)
            if len(key) == 44:
                cnpj_digits = key[6:20]
                vals["vat"] = utils.mask_cnpj(cnpj_digits)
                vals["serie"] = key[22:25].lstrip("0") or "0"
                vals["document_number"] = key[25:34].lstrip("0") or "0"
            document = Document.create(vals)
        return document
