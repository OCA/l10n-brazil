# Copyright 2026 Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import logging
import os
import re
import tempfile
from datetime import timedelta

from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    pkcs12,
)

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal_dfe.constants.dfe import (
    CSTAT_CONSUMO_INDEVIDO,
    CSTAT_NO_DOCS,
    CSTAT_SUCCESS,
)
from odoo.addons.l10n_br_fiscal_dfe.tools import utils

from ..constants.nfse_dfe import (
    NFSE_ADN_BASE_URLS,
    NFSE_ADN_DFE_PATH,
    NFSE_ADN_NFSE_PATH,
    NFSE_EVENT_DOCUMENT_TYPES,
    NFSE_LOTE_SIZE,
    NFSE_MAX_PAGES,
    NFSE_NOTE_TYPES,
    NFSE_SEFIN_BASE_URLS,
    NFSE_SEFIN_NFSE_PATH,
    NFSE_SKIP_DOCUMENT_TYPES,
    NFSE_STATE_AUTHORIZED,
    NFSE_STATE_CANCELLED,
)
from ..services.adn_dfe import AdnDfeClient
from ..services.nfse_xml import (
    decode_arquivo_xml,
    is_cancel_event,
    normalize_access_key,
    normalize_event_code,
    parse_nfse_event_xml,
    parse_nfse_xml,
    xml_root_is_nfse,
)

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    nfse_dfe_environment = fields.Selection(
        selection=[
            ("producao", "Production"),
            ("producao_restrita", "Restricted Production"),
        ],
        string="NFS-e ADN Environment",
        default="producao_restrita",
        required=True,
        help="Environment of the national NFS-e distribution API (ADN). "
        "This is not the municipal NFS-e emission environment.",
    )
    nfse_last_nsu = fields.Char(string="NFS-e Last NSU", size=25, default="0")
    nfse_max_nsu = fields.Char(string="NFS-e Max NSU", readonly=True)
    nfse_dfe_last_query = fields.Datetime(string="NFS-e DF-e Last Query")
    nfse_dfe_last_status = fields.Char(string="NFS-e DF-e Last Status", readonly=True)
    nfse_dfe_last_status_code = fields.Char(
        string="NFS-e DF-e Last Status Code", readonly=True
    )
    nfse_dfe_next_query = fields.Datetime(
        string="NFS-e Next Scheduled Query",
        help="NFS-e distribution will not be queried before this time.",
    )
    nfse_auto_fetch = fields.Boolean(
        string="Auto-fetch NFS-e",
        help="Periodically query the ADN for NFS-e documents issued to this company.",
    )
    nfse_import_product_id = fields.Many2one(
        comodel_name="product.product",
        string="Default NFS-e Import Product",
        domain="[('type', '=', 'service')]",
        help="Service product applied when a national NFS-e is imported "
        "and the wizard has no product yet.",
    )

    def _dfe_document_distribution(self, fiscal_type):
        if fiscal_type == "nfse":
            return self._nfse_document_distribution()
        return super()._dfe_document_distribution(fiscal_type)

    def _dfe_search_specific_document(self, fiscal_type, access_key=None, nsu=None):
        if fiscal_type == "nfse":
            return self._nfse_search_specific(access_key=access_key, nsu=nsu)
        return super()._dfe_search_specific_document(
            fiscal_type, access_key=access_key, nsu=nsu
        )

    def _dfe_cron_xmlid(self, fiscal_type):
        if fiscal_type == "nfse":
            return "l10n_br_nfse_dfe.ir_cron_search_nfse_dfe_documents"
        return super()._dfe_cron_xmlid(fiscal_type)

    def _dfe_document_action_xmlid(self, fiscal_type):
        if fiscal_type == "nfse":
            return "l10n_br_nfse_dfe.action_nfse_dfe_document"
        return super()._dfe_document_action_xmlid(fiscal_type)

    def action_nfse_document_distribution(self):
        self.ensure_one()
        return self.action_document_distribution("nfse")

    def action_nfse_search_specific(self):
        self.ensure_one()
        return self.action_search_specific("nfse")

    @api.model
    def action_banner_search_all_nfse(self):
        company = self.env.company
        result = company.action_document_distribution("nfse")
        return result or {"type": "ir.actions.client", "tag": "reload"}

    @api.model
    def action_banner_specific_search_nfse(self):
        return self.env.company.action_search_specific("nfse")

    def _nfse_adn_base_url(self):
        self.ensure_one()
        return NFSE_ADN_BASE_URLS.get(
            self.nfse_dfe_environment, NFSE_ADN_BASE_URLS["producao_restrita"]
        )

    def _nfse_query_params(self):
        self.ensure_one()
        params = {"lote": "true"}
        cnpj = re.sub(r"\D", "", self.vat or "")
        if cnpj:
            params["cnpjConsulta"] = cnpj
        return params

    def _nfse_certificate_pem(self):
        self.ensure_one()
        certificate = self._get_br_certificate(only_ecnpj=True)
        if not certificate or not certificate.content:
            raise UserError(
                _("Configure an e-CNPJ certificate before querying the ADN.")
            )
        pfx = base64.b64decode(certificate.with_context(bin_size=False).content)
        password = certificate.pkcs12_password or None
        password_bytes = password.encode() if isinstance(password, str) else password
        key, cert, _extra = pkcs12.load_key_and_certificates(pfx, password_bytes)
        if not key or not cert:
            raise UserError(_("The e-CNPJ certificate could not be read."))
        pem = key.private_bytes(
            Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption()
        )
        pem += cert.public_bytes(Encoding.PEM)
        return pem

    def _nfse_sefin_base_url(self):
        self.ensure_one()
        return NFSE_SEFIN_BASE_URLS.get(
            self.nfse_dfe_environment, NFSE_SEFIN_BASE_URLS["producao_restrita"]
        )

    def _nfse_http_get(self, base_url, path, params=None):
        """GET one mTLS resource with the company e-CNPJ."""
        self.ensure_one()
        pem = self._nfse_certificate_pem()
        fd, pem_path = tempfile.mkstemp(suffix=".pem")
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(pem)
            client = AdnDfeClient(base_url, pem_path)
            return client.get(path, params=params)
        finally:
            try:
                os.unlink(pem_path)
            except OSError:
                _logger.debug("Temporary NFS-e certificate file was already removed")

    def _nfse_adn_request(self, path, params=None):
        """GET one ADN distribution resource with the company e-CNPJ."""
        return self._nfse_http_get(self._nfse_adn_base_url(), path, params=params)

    def _nfse_sefin_request(self, path):
        """GET one Sefin Nacional resource with the company e-CNPJ."""
        return self._nfse_http_get(self._nfse_sefin_base_url(), path)

    def _nfse_current_nsu(self):
        raw = str(self._dfe_get_typed_value("nfse", "last_nsu") or "0")
        digits = re.sub(r"\D", "", raw) or "0"
        return str(int(digits))

    def _nfse_distribution_on_cooldown(self):
        next_query = self._dfe_get_typed_value("nfse", "dfe_next_query")
        return bool(next_query and next_query > fields.Datetime.now())

    def _nfse_document_ids(self):
        return set(
            self.env["l10n_br_fiscal_dfe.document"]
            .sudo()
            .search([("company_id", "=", self.id), ("fiscal_type", "=", "nfse")])
            .ids
        )

    def _nfse_document_distribution(self):
        """Pull the next ADN batches and store them in the DF-e inbox."""
        self.ensure_one()
        if self._nfse_distribution_on_cooldown():
            return
        existing_ids = self._nfse_document_ids()
        last_nsu = self._nfse_current_nsu()
        status = CSTAT_NO_DOCS
        message = _("No NFS-e documents found.")
        caught_up = False
        had_exception = False
        try:
            for _page in range(NFSE_MAX_PAGES):
                response = self._nfse_adn_request(
                    f"{NFSE_ADN_DFE_PATH}/{int(last_nsu)}",
                    params=self._nfse_query_params(),
                )
                outcome = self._nfse_handle_page(response, last_nsu)
                last_nsu = outcome["last_nsu"]
                status = outcome["status"]
                message = outcome["message"]
                caught_up = outcome["caught_up"]
                if outcome.get("retry_after") is not None:
                    self._nfse_schedule_retry(last_nsu, status, message, outcome)
                    self._nfse_notify_new(existing_ids)
                    return
                if not outcome["continue"]:
                    break
        except Exception as error:
            had_exception = True
            status = ""
            message = _("Error searching NFS-e documents.\n%(error)s", error=error)
            self._dfe_log(message, log_type="error", fiscal_type="nfse")
        self._nfse_store_cursor(last_nsu, status, message, caught_up=caught_up)
        self._dfe_schedule_next_query(
            status_code=status,
            fiscal_type="nfse",
            had_exception=had_exception,
        )
        self._nfse_notify_new(existing_ids)

    def _nfse_handle_page(self, response, last_nsu):
        if response.status_code == 404:
            self._dfe_log(
                _("No more NFS-e documents (HTTP 404)."),
                log_type="info",
                fiscal_type="nfse",
            )
            return self._nfse_page_outcome(
                last_nsu, CSTAT_NO_DOCS, _("No NFS-e documents found."), caught_up=True
            )
        if response.status_code == 429:
            return self._nfse_rate_limit_outcome(response, last_nsu)
        if not response.ok:
            message = self._nfse_error_detail(response)
            self._dfe_log(message, log_type="warning", fiscal_type="nfse")
            return self._nfse_page_outcome(last_nsu, "", message)
        items = self._nfse_lote(response)
        if not items:
            self._dfe_log(
                _("ADN returned an empty NFS-e batch."),
                log_type="info",
                fiscal_type="nfse",
            )
            return self._nfse_page_outcome(
                last_nsu, CSTAT_NO_DOCS, _("No NFS-e documents found."), caught_up=True
            )
        highest = self._nfse_process_items(items)
        if not highest or int(highest) <= int(last_nsu):
            return self._nfse_page_outcome(
                last_nsu,
                CSTAT_SUCCESS,
                _("NFS-e distribution did not advance the NSU."),
                caught_up=True,
            )
        self._dfe_log(
            _("NFS-e distribution OK (ultNSU=%(nsu)s).", nsu=highest),
            log_type="success",
            fiscal_type="nfse",
        )
        return self._nfse_page_outcome(
            str(int(highest)),
            CSTAT_SUCCESS,
            _("Documents found."),
            continue_loop=len(items) >= NFSE_LOTE_SIZE,
            caught_up=len(items) < NFSE_LOTE_SIZE,
        )

    def _nfse_page_outcome(
        self, last_nsu, status, message, continue_loop=False, caught_up=False
    ):
        return {
            "continue": continue_loop,
            "last_nsu": str(last_nsu),
            "status": status,
            "message": message,
            "caught_up": caught_up,
        }

    def _nfse_rate_limit_outcome(self, response, last_nsu):
        self._dfe_log(
            _("ADN rate limit (HTTP 429). Next query respects Retry-After."),
            log_type="warning",
            fiscal_type="nfse",
        )
        outcome = self._nfse_page_outcome(
            last_nsu,
            CSTAT_CONSUMO_INDEVIDO,
            _("Rate limited by the ADN."),
        )
        outcome["retry_after"] = self._nfse_retry_after_seconds(response)
        return outcome

    def _nfse_schedule_retry(self, last_nsu, status, message, outcome):
        self._nfse_store_cursor(last_nsu, status, message, caught_up=False)
        seconds = outcome.get("retry_after") or 0
        if seconds:
            when = fields.Datetime.now() + timedelta(seconds=seconds)
            self._dfe_write_typed("nfse", {"dfe_next_query": when})
            self._dfe_sync_cron_nextcall("nfse")
            return
        self._dfe_schedule_next_query(CSTAT_CONSUMO_INDEVIDO, "nfse")

    def _nfse_store_cursor(self, last_nsu, status, message, caught_up=False):
        formatted = utils.format_nsu(last_nsu) or "0"
        vals = {
            "last_nsu": formatted,
            "dfe_last_query": fields.Datetime.now(),
            "dfe_last_status": message or "",
            "dfe_last_status_code": status or "",
        }
        if caught_up:
            vals["max_nsu"] = formatted
        self._dfe_write_typed("nfse", vals)

    def _nfse_notify_new(self, existing_ids):
        new_ids = self._nfse_document_ids() - existing_ids
        if not new_ids:
            return
        documents = self.env["l10n_br_fiscal_dfe.document"].sudo().browse(list(new_ids))
        self._dfe_notify_users(documents, "nfse")

    def _nfse_lote(self, response):
        body = response.body or {}
        lote = body.get("LoteDFe") or body.get("loteDFe") or []
        if isinstance(lote, dict):
            return [lote]
        return list(lote)

    def _nfse_error_detail(self, response):
        body = response.body or {}
        parts = []
        for error in body.get("Erros") or body.get("erros") or []:
            if isinstance(error, dict):
                code = error.get("Codigo") or ""
                description = error.get("Descricao") or error
                parts.append(f"{code}: {description}")
        if parts:
            return "; ".join(parts)
        message = body.get("mensagem") or body.get("message")
        if message:
            return str(message)
        return (response.text or str(response.status_code))[:500]

    @staticmethod
    def _nfse_retry_after_seconds(response):
        headers = response.headers or {}
        raw = headers.get("Retry-After") or headers.get("retry-after")
        if raw and str(raw).strip().isdigit():
            return int(str(raw).strip())
        return 0

    def _nfse_process_items(self, items):
        skipped = []
        notes = []
        events = []
        for item in items:
            tipo = str(item.get("TipoDocumento") or "").strip().upper()
            if tipo in NFSE_SKIP_DOCUMENT_TYPES:
                skipped.append(item)
            elif self._nfse_item_is_event(item):
                events.append(item)
            else:
                notes.append(item)
        highest = 0
        # Notes first, then events, so a cancellation can see its document.
        # A bad item must not abort the page or freeze the NSU cursor.
        for item in skipped + notes + events:
            nsu = self._nfse_process_item_safe(item)
            if nsu > highest:
                highest = nsu
        return utils.format_nsu(highest) if highest else False

    def _nfse_process_item_safe(self, item):
        try:
            with self.env.cr.savepoint():
                return self._nfse_process_item(item)
        except Exception as error:
            nsu = item.get("NSU")
            # One line, without a traceback. The test that forces this path
            # mutes the logger: the OCA checklog fails on a warning from here.
            _logger.warning("Skipping NFS-e DF-e item NSU %s: %s", nsu, error)
            self._dfe_log(
                _(
                    "NFS-e item NSU %(nsu)s was skipped: %(error)s",
                    nsu=nsu,
                    error=error,
                ),
                log_type="warning",
                fiscal_type="nfse",
            )
            digits = re.sub(r"\D", "", str(nsu or ""))
            return int(digits or "0")

    def _nfse_item_is_event(self, item):
        tipo = str(item.get("TipoDocumento") or "").strip().upper()
        if tipo in NFSE_NOTE_TYPES or tipo in NFSE_SKIP_DOCUMENT_TYPES:
            return False
        if tipo in NFSE_EVENT_DOCUMENT_TYPES or item.get("TipoEvento"):
            return True
        xml_bytes = decode_arquivo_xml(item.get("ArquivoXml"))
        if xml_root_is_nfse(xml_bytes):
            return False
        event = parse_nfse_event_xml(xml_bytes) or {}
        return bool(event.get("event_type") or event.get("access_key"))

    def _nfse_process_item(self, item):
        tipo = str(item.get("TipoDocumento") or "").strip().upper()
        nsu = utils.format_nsu(item.get("NSU"))
        if tipo in NFSE_SKIP_DOCUMENT_TYPES:
            digits = re.sub(r"\D", "", nsu or "")
            return int(digits or "0")
        xml_bytes = decode_arquivo_xml(item.get("ArquivoXml"))
        if self._nfse_item_is_event(item):
            self._nfse_create_event(item, xml_bytes, nsu)
        else:
            self._nfse_create_note(item, xml_bytes, nsu)
        digits = re.sub(r"\D", "", nsu or "")
        return int(digits or "0")

    def _nfse_find_existing_dfe(self, nsu, access_key, schema):
        dfe_model = self.env["l10n_br_fiscal_dfe.dfe"].sudo()
        if self._dfe_is_valid_nsu(nsu):
            found = dfe_model.search(
                [
                    ("nsu", "=", nsu),
                    ("company_id", "=", self.id),
                    ("fiscal_type", "=", "nfse"),
                ],
                limit=1,
            )
            if found:
                return found
        if not access_key:
            return dfe_model.browse()
        schemas = {schema}
        if str(schema or "").upper() == "EVENTO":
            # Older rows stored the event schema in lower case.
            schemas.add("evento")
        return dfe_model.search(
            [
                ("access_key", "=", access_key),
                ("company_id", "=", self.id),
                ("fiscal_type", "=", "nfse"),
                ("schema_type", "in", list(schemas)),
            ],
            limit=1,
        )

    def _nfse_create_note(self, item, xml_bytes, nsu):
        parsed = parse_nfse_xml(xml_bytes) or {}
        access_key = normalize_access_key(item.get("ChaveAcesso")) or parsed.get(
            "access_key"
        )
        if not access_key:
            self._dfe_log(
                _("NFS-e item without a 50-digit access key was skipped."),
                log_type="warning",
                fiscal_type="nfse",
            )
            return
        if self._nfse_find_existing_dfe(nsu, access_key, "NFSe"):
            return
        document = self._dfe_get_or_create_document(access_key, "nfse")
        dfe_record = (
            self.env["l10n_br_fiscal_dfe.dfe"]
            .sudo()
            .create(
                {
                    "access_key": access_key,
                    "nsu": nsu or False,
                    "company_id": self.id,
                    "fiscal_type": "nfse",
                    "document_type_dfe": "complete",
                    "schema_type": "NFSe",
                }
            )
        )
        document.sudo().dfe_ids = [(4, dfe_record.id)]
        document._update_metadata(self._nfse_note_metadata(parsed), is_complete=True)
        if xml_bytes:
            dfe_record.create_xml_attachment(xml_bytes)
        # A cancellation may already be in the inbox. Do not put the note
        # back to authorized in that case.
        self._nfse_sync_document_state(document)

    def _nfse_note_metadata(self, parsed):
        serie = (parsed.get("serie") or "").lstrip("0")[:5]
        emitter = (parsed.get("provider_name") or "")[:60]
        provider_cnpj = parsed.get("provider_cnpj")
        metadata = {"document_state": NFSE_STATE_AUTHORIZED}
        if emitter:
            metadata["emitter"] = emitter
        if provider_cnpj:
            metadata["vat"] = utils.mask_cnpj(provider_cnpj)
        if serie:
            metadata["serie"] = serie
        if parsed.get("number"):
            metadata["document_number"] = str(parsed["number"])[:18]
        if parsed.get("service_value"):
            metadata["document_amount"] = parsed["service_value"]
        if parsed.get("emission_date"):
            metadata["document_emission_date"] = parsed["emission_date"]
        return metadata

    def _nfse_create_event(self, item, xml_bytes, nsu):
        parsed = parse_nfse_event_xml(xml_bytes) or {}
        access_key = normalize_access_key(item.get("ChaveAcesso")) or parsed.get(
            "access_key"
        )
        if not access_key:
            self._dfe_log(
                _("NFS-e event without a 50-digit access key was skipped."),
                log_type="warning",
                fiscal_type="nfse",
            )
            return
        schema = str(item.get("TipoDocumento") or "EVENTO").strip().upper()
        if schema not in NFSE_EVENT_DOCUMENT_TYPES:
            schema = "EVENTO"
        if self._nfse_find_existing_dfe(nsu, access_key, schema):
            return
        raw_type = item.get("TipoEvento") or parsed.get("event_type") or ""
        event_type = normalize_event_code(raw_type) or str(raw_type)
        document = self._dfe_get_or_create_document(access_key, "nfse")
        dfe_record = (
            self.env["l10n_br_fiscal_dfe.dfe"]
            .sudo()
            .create(
                {
                    "access_key": access_key,
                    "nsu": nsu or False,
                    "company_id": self.id,
                    "fiscal_type": "nfse",
                    "document_type_dfe": "event",
                    "schema_type": schema,
                    "event_type_dfe": event_type,
                }
            )
        )
        document.sudo().dfe_ids = [(4, dfe_record.id)]
        if xml_bytes:
            dfe_record.create_xml_attachment(xml_bytes)
        self._nfse_sync_document_state(document)

    def _nfse_sync_document_state(self, document):
        """Set the note state from registered cancellation events.

        A request (``PEDIDO_REGISTRO_EVENTO``) and a denied request do not
        change the note. Called after the note and after the event, so the
        arrival order does not matter.
        """
        cancelled = document.dfe_ids.filtered(
            lambda rec: rec.document_type_dfe == "event"
            and (rec.schema_type or "").upper() == "EVENTO"
            and is_cancel_event(rec.event_type_dfe)
        )
        state = NFSE_STATE_CANCELLED if cancelled else NFSE_STATE_AUTHORIZED
        if document.document_state != state:
            document.sudo().write({"document_state": state})

    def _nfse_search_specific(self, access_key=None, nsu=None):
        self.ensure_one()
        if access_key:
            self._nfse_fetch_by_access_key(access_key)
            return
        nsu_int = int(re.sub(r"\D", "", nsu or "0") or "0")
        response = self._nfse_adn_request(
            f"{NFSE_ADN_DFE_PATH}/{max(nsu_int - 1, 0)}",
            params=self._nfse_query_params(),
        )
        self._nfse_raise_for_status(response)
        wanted = utils.format_nsu(nsu_int)
        match = [
            item
            for item in self._nfse_lote(response)
            if utils.format_nsu(item.get("NSU")) == wanted
        ]
        if not match:
            raise UserError(
                _(
                    "NFS-e NSU %(nsu)s was not found in the ADN response.",
                    nsu=nsu,
                )
            )
        self._nfse_process_item(match[0])

    def _nfse_fetch_by_access_key(self, access_key):
        """Load one NFS-e from Sefin Nacional and its events from the ADN.

        ``GET /contribuintes/NFSe/{chave}`` is not a documented ADN route and
        answers 404. The note lives on Sefin ``GET /nfse/{chave}``.
        """
        response = self._nfse_sefin_request(f"{NFSE_SEFIN_NFSE_PATH}/{access_key}")
        self._nfse_raise_for_status(response)
        self._nfse_process_item(self._nfse_item_from_sefin(response, access_key))
        events = self._nfse_adn_request(f"{NFSE_ADN_NFSE_PATH}/{access_key}/Eventos")
        if events.status_code == 404:
            return
        self._nfse_raise_for_status(events)
        for item in self._nfse_lote(events):
            tipo = str(item.get("TipoDocumento") or "").strip().upper()
            if tipo in NFSE_NOTE_TYPES:
                continue
            self._nfse_process_item(item)

    def _nfse_item_from_sefin(self, response, access_key):
        body = response.body or {}
        packed = body.get("nfseXmlGZipB64")
        if not packed:
            raise UserError(_("The Sefin Nacional response does not contain an NFS-e."))
        return {
            "NSU": "0",
            "ChaveAcesso": body.get("chaveAcesso") or access_key,
            "TipoDocumento": "NFSE",
            "ArquivoXml": packed,
        }

    def _nfse_raise_for_status(self, response):
        if response.status_code == 404:
            raise UserError(_("This NFS-e was not found."))
        if response.status_code == 429:
            raise UserError(_("The service rate limit is active. Try again later."))
        if not response.ok:
            raise UserError(self._nfse_error_detail(response))
