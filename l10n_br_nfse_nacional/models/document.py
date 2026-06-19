# Copyright 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging
from datetime import datetime

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_ENVIADA,
    SITUACAO_EDOC_REJEITADA,
)
from odoo.addons.l10n_br_fiscal_edi.models.document import Document as FiscalDocument
from odoo.addons.l10n_br_nfse.models.document import filter_processador_edoc_nfse
from odoo.addons.l10n_br_nfse_spec.models.spec_mixin import DpsBuilder

from ..constants.nfse_nacional import (
    ADN_URL,
    API_ENDPOINT_ADN,
    API_ENDPOINT_DANFSE,
    API_ENDPOINT_NACIONAL,
    CODE_NFE_AUTORIZADA,
    DANFSE_URL,
    PDF_FOOTER,
    PDF_HEADER,
    SEFIN_URL,
    STATUS_AUTORIZADO,
    STATUS_CANCELADO,
    STATUS_ERRO,
    TIMEOUT,
)

_logger = logging.getLogger(__name__)


def filter_processador_nfse_nacional(record):
    """Return True when the record belongs to the nfse_nacional provider."""
    return (
        filter_processador_edoc_nfse(record)
        and record.company_id.provedor_nfse == "nfse_nacional"
    )


def _is_valid_pdf(content):
    """Return True if content is a valid PDF byte stream."""
    return content.startswith(PDF_HEADER) and content.strip().endswith(PDF_FOOTER)


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    nfse_nacional_chave = fields.Char(
        string="NFS-e Nacional Access Key",
        readonly=True,
        copy=False,
        help="44-digit access key for the NFS-e Nacional returned by SEFIN.",
    )

    nfse_nacional_rps_substituido = fields.Char(
        string="Substituted RPS Number",
        copy=False,
        help="RPS/NFS-e number being substituted (for replacement notes).",
    )

    def make_pdf(self):
        """Generate the DANFSE Nacional using brazilfiscalreport.

        Renders from the authorized NFS-e XML stored in authorization_file_id.
        Falls back to fetching the XML from the ADN service when the attachment
        is not yet available.

        Overrides l10n_br_nfse; non-nacional documents fall through to super().
        """
        if not self.filtered(filter_processador_nfse_nacional):
            return super().make_pdf()

        for record in self.filtered(filter_processador_nfse_nacional):
            xml_bytes = record._get_nfse_xml_bytes()
            if not xml_bytes:
                _logger.warning(
                    "DANFSE: no authorized XML available for document %s",
                    record.id,
                )
                continue
            try:
                from brazilfiscalreport.danfse import Danfse

                pdf_bytes = bytes(Danfse(xml_bytes).output())
            except Exception as exc:
                _logger.warning(
                    "DANFSE: brazilfiscalreport failed for document %s: %s",
                    record.id,
                    exc,
                )
                continue
            record._attach_pdf(pdf_bytes)

    def _get_nfse_xml_bytes(self):
        """Return the authorized NFS-e Nacional XML as bytes.

        Tries the stored authorization attachment first, then fetches from ADN.
        """
        self.ensure_one()
        if self.authorization_file_id:
            return base64.b64decode(self.authorization_file_id.datas)
        if self.nfse_nacional_chave:
            xml_str = self._fetch_xml_from_adn(self.nfse_nacional_chave)
            return xml_str.encode("utf-8") if xml_str else None
        return None

    def _attach_pdf(self, pdf_content):
        """Attach raw PDF bytes to the document as an ir.attachment.

        Args:
            pdf_content (bytes): Raw PDF bytes to attach.
        """
        filename = (
            "NFS-e-Nacional-" + self.document_number + ".pdf"
            if self.document_number
            else "RPS-Nacional-" + (self.rps_number or "") + ".pdf"
        )
        vals = {
            "name": filename,
            "res_model": self._name,
            "res_id": self.id,
            "datas": base64.b64encode(pdf_content),
            "mimetype": "application/pdf",
            "type": "binary",
        }
        if self.file_report_id:
            self.file_report_id.write(vals)
        else:
            self.file_report_id = self.env["ir.attachment"].create(vals)

    def _api_request(self, base_url, method, path, data=None, session=None):
        """Perform an authenticated HTTP request against an NFS-e Nacional API.

        Uses the company mTLS session. Sends data as JSON when provided and
        always requests JSON back via Accept header.

        Args:
            base_url (str): Base URL (SEFIN_URL, ADN_URL, DANFSE_URL, …).
            method (str): HTTP verb ('GET', 'POST', 'DELETE').
            path (str): URL path appended to base_url.
            data (dict, optional): JSON-serializable request body.
            session: Reusable requests.Session; fetched from company when omitted.

        Returns:
            requests.Response

        Raises:
            UserError: On connection or network errors.
        """
        if session is None:
            session = self.company_id._get_sefin_session()
        url = base_url + path
        try:
            return session.request(
                method,
                url,
                json=data,
                headers={"Accept": "application/json"},
                timeout=TIMEOUT,
            )
        except Exception as exc:
            raise UserError(
                _("Error communicating with NFS-e Nacional API " "(%(url)s): %(error)s")
                % {"url": url, "error": exc}
            ) from exc

    def _sefin_request(self, record, method, endpoint_key, suffix="", data=None):
        """Perform a request against the SEFIN Nacional API (issue/query/cancel).

        Args:
            record: Document record providing environment and company.
            method (str): HTTP verb.
            endpoint_key (str): Key in API_ENDPOINT_NACIONAL.
            suffix (str): Appended to the endpoint path (e.g. access key).
            data (dict, optional): JSON body.

        Returns:
            requests.Response
        """
        path = API_ENDPOINT_NACIONAL[endpoint_key] + suffix
        return record._api_request(
            SEFIN_URL[record.nfse_environment], method, path, data=data
        )

    def _fetch_danfse_from_service(self, chave):
        """Download the DANFSE PDF from the official DANFSE service.

        Endpoint: DANFSE_URL[env] + /danfse/{chave}

        Args:
            chave (str): 44-digit NFS-e Nacional access key.

        Returns:
            bytes or None: PDF bytes when valid, None on any failure.
        """
        if not chave:
            return None
        path = API_ENDPOINT_DANFSE["render"] + chave
        try:
            response = self._api_request(DANFSE_URL[self.nfse_environment], "GET", path)
            if response.status_code == 200 and _is_valid_pdf(response.content):
                return response.content
        except Exception as exc:
            _logger.warning("DANFSE service unavailable for %s: %s", chave, exc)
        return None

    def _fetch_xml_from_adn(self, chave):
        """Download the NFS-e XML from the ADN (Ambiente de Distribuição) service.

        Endpoint: ADN_URL[env] + /contribuintes/nfse/{chave}

        Args:
            chave (str): 44-digit NFS-e Nacional access key.

        Returns:
            str: XML text, or empty string on any failure.
        """
        if not chave:
            return ""
        path = API_ENDPOINT_ADN["contributor_nfse"] + chave
        try:
            response = self._api_request(ADN_URL[self.nfse_environment], "GET", path)
            if response.status_code == 200:
                return response.content.decode("utf-8")
        except Exception as exc:
            _logger.warning("ADN XML fetch failed for %s: %s", chave, exc)
        return ""

    def _prepare_dps_payload(self):
        """Assemble the DPS v1.0 JSON payload for the SEFIN NFS-e Nacional API.

        Delegates to DpsBuilder from l10n_br_nfse_spec, which maps the inherited
        _prepare_lote_rps(), _prepare_dados_servico(), and _prepare_dados_tomador()
        outputs to the nested DPS XSD structure expected by the SEFIN REST endpoint.

        Returns:
            dict: Nested DPS payload ({"infDPS": {...}}) ready to POST as JSON.
        """
        return DpsBuilder(self).build()

    def _document_export(self, pretty_print=True):
        """Create the initial authorization event, bypassing the OCA SOAP factory.

        l10n_br_nfse uses erpbrasil's NFSeFactory (SOAP); we use REST/JSON, so we
        call super() on FiscalDocument directly to skip that factory while still
        running the fiscal EDI export logic.
        """
        if self.filtered(filter_processador_nfse_nacional):
            result = super(FiscalDocument, self)._document_export()
        else:
            result = super()._document_export()

        for record in self.filtered(filter_processador_nfse_nacional):
            event_id = record.event_ids.create_event_save_xml(
                company_id=record.company_id,
                environment=(
                    EVENT_ENV_PROD if record.nfse_environment == "1" else EVENT_ENV_HML
                ),
                event_type="0",
                xml_file="",
                document_id=record,
            )
            record.authorization_event_id = event_id

        return result

    def _eletronic_document_send(self):
        """Send the DPS to SEFIN for each nfse_nacional document."""
        res = super()._eletronic_document_send()
        for record in self.filtered(filter_processador_nfse_nacional):
            record._process_send_nacional(record)
        return res

    def _document_status(self):
        """Query SEFIN for the current status of each nfse_nacional document."""
        result = super()._document_status()
        for record in self.filtered(filter_processador_nfse_nacional):
            result = record._process_status_nacional(record)
        return result

    def _exec_before_SITUACAO_EDOC_CANCELADA(self, old_state, new_state):
        """Cancel the NFS-e Nacional on SEFIN before transitioning to cancelled."""
        result = super()._exec_before_SITUACAO_EDOC_CANCELADA(old_state, new_state)
        for record in self.filtered(filter_processador_nfse_nacional):
            record._cancel_nfse_nacional(record)
        return result

    def _process_send_nacional(self, record):
        """POST the DPS to SEFIN and handle the authorization response.

        HTTP 200/201 → authorized immediately.
        HTTP 202      → async processing, transitions to ENVIADA.
        HTTP 422 with already-authorized code → triggers a status query.
        Other codes   → transitions to REJEITADA with the error message.

        Args:
            record: The document record to send.
        """
        payload = record._prepare_dps_payload()
        response = record._sefin_request(record, "POST", "issue", data=payload)
        try:
            json_data = response.json() if response.content else {}
        except Exception:
            json_data = {}

        if response.status_code in (200, 201):
            record._process_authorized_status_nacional(record, json_data)
        elif response.status_code == 202:
            if record.state_edoc == SITUACAO_EDOC_REJEITADA:
                record.state_edoc = SITUACAO_EDOC_ENVIADA
            else:
                record._change_state(SITUACAO_EDOC_ENVIADA)
        elif response.status_code == 422:
            code = json_data.get("codigo", "")
            if code == CODE_NFE_AUTORIZADA:
                record._document_status()
            else:
                erros = json_data.get("erros", [])
                msg = (
                    erros[0]["mensagem"]
                    if erros
                    else json_data.get("mensagem", _("Unknown error"))
                )
                record.write({"edoc_error_message": msg})
                record._change_state(SITUACAO_EDOC_REJEITADA)
        else:
            msg = json_data.get("mensagem", str(response.status_code))
            record.write({"edoc_error_message": msg})
            record._change_state(SITUACAO_EDOC_REJEITADA)

    def _process_status_nacional(self, record):
        """Query SEFIN for the document status and update the record state.

        Args:
            record: The document record to query.

        Returns:
            str: Translated status string.
        """
        ref = record.nfse_nacional_chave or str(record.rps_number)
        response = record._sefin_request(record, "GET", "query", suffix=ref)

        if response.status_code != 200:
            return _("Unable to retrieve the document status.")

        try:
            json_data = response.json() if response.content else {}
        except Exception:
            json_data = {}
        status = json_data.get("status", "")

        edoc_states = [SITUACAO_EDOC_ENVIADA, SITUACAO_EDOC_REJEITADA]
        if record.company_id.nfse_nacional_update_authorized_status:
            edoc_states.append(SITUACAO_EDOC_AUTORIZADA)

        if record.state_edoc in edoc_states:
            if (
                status == STATUS_AUTORIZADO
                and record.state_edoc != SITUACAO_EDOC_AUTORIZADA
            ):
                record._process_authorized_status_nacional(record, json_data)
            elif status == STATUS_ERRO:
                record._process_error_status(record, json_data)
            elif (
                status == STATUS_CANCELADO
                and record.state_edoc != SITUACAO_EDOC_CANCELADA
            ):
                record._document_cancel(record.cancel_reason)

        return _(status)

    def _process_authorized_status_nacional(self, record, json_data):
        """Update the record with authorization data from SEFIN and finalize the event.

        Fetches the NFS-e XML from the ADN service and the DANFSE PDF from the
        official DANFSE service. Falls back to brazilfiscalreport when the
        DANFSE service is unavailable or force_odoo_danfse is enabled.

        Args:
            record: The document record to update.
            json_data (dict): JSON response from SEFIN containing authorization data.
        """
        raw = json_data.get("data_emissao", "")
        try:
            naive_dt = (
                datetime.strptime(raw, "%Y-%m-%dT%H:%M:%S%z")
                .astimezone(pytz.utc)
                .replace(tzinfo=None)
            )
        except Exception:
            naive_dt = fields.Datetime.now()

        access_key = json_data.get("chave_nfse", "") or json_data.get("chave", "")
        record.write(
            {
                "verify_code": json_data.get("codigo_verificacao", ""),
                "document_number": json_data.get("numero", ""),
                "authorization_date": naive_dt,
                "nfse_nacional_chave": access_key,
            }
        )

        if not record.authorization_event_id:
            record._document_export()

        if record.authorization_event_id:
            xml = record._fetch_xml_from_adn(access_key)
            record.authorization_event_id.set_done(
                status_code=4,
                response=_("Successfully Processed"),
                protocol_date=record.authorization_date,
                protocol_number=record.authorization_protocol,
                file_response_xml=xml,
            )
            record._change_state(SITUACAO_EDOC_AUTORIZADA)

            if record.company_id.nfse_nacional_force_odoo_danfse:
                record.make_pdf()
            else:
                pdf_content = record._fetch_danfse_from_service(access_key)
                if pdf_content:
                    record._attach_pdf(pdf_content)
                else:
                    record.make_pdf()

    def _process_error_status(self, record, json_data):
        """Transition the document to REJEITADA and store the error message.

        Args:
            record: The document record.
            json_data (dict): JSON response containing 'erros' list.
        """
        erros = json_data.get("erros", [])
        msg = erros[0]["mensagem"] if erros else _("Authorization error")
        record.write({"edoc_error_message": msg})
        record._change_state(SITUACAO_EDOC_REJEITADA)

    def _cancel_nfse_nacional(self, record):
        """Send a cancellation request to SEFIN for the given document.

        Checks current status first — if already cancelled on SEFIN, creates the
        cancel event locally without sending a new DELETE. Otherwise sends DELETE
        and handles the response.

        Args:
            record: The document record to cancel.

        Raises:
            UserError: When SEFIN returns an unexpected error response.
        """
        ref = record.nfse_nacional_chave or str(record.rps_number)

        status_response = record._sefin_request(record, "GET", "query", suffix=ref)
        if (
            status_response.status_code == 200
            and status_response.json().get("status") == STATUS_CANCELADO
        ):
            record._create_cancel_event(record)
            return

        response = record._sefin_request(
            record,
            "DELETE",
            "cancel",
            suffix=ref,
            data={"justificativa": record.cancel_reason or _("Cancelled by user")},
        )
        json_data = response.json()

        if response.status_code in (200, 400):
            code = json_data.get("codigo", "")
            status = json_data.get("status", "")
            if not code:
                code = (json_data.get("erros") or [{}])[0].get("codigo", "")
            if code == "nfe_cancelada" or status == STATUS_CANCELADO:
                record._create_cancel_event(record)
                return

        raise UserError(
            _(
                "%(code)s - %(msg)s",
                code=response.status_code,
                msg=json_data.get("mensagem", ""),
            )
        )

    def _create_cancel_event(self, record):
        """Create and finalize the cancellation event on the document.

        Args:
            record: The document record.
        """
        event = record.event_ids.create_event_save_xml(
            company_id=record.company_id,
            environment=(
                EVENT_ENV_PROD if record.nfse_environment == "1" else EVENT_ENV_HML
            ),
            event_type="2",
            xml_file="",
            document_id=record,
        )
        event.set_done(
            status_code=4,
            response=_("Successfully Processed"),
            protocol_date=fields.Datetime.to_string(fields.Datetime.now()),
            protocol_number="",
            file_response_xml="",
        )
        record.cancel_event_id = event

    @api.model
    def _cron_document_status_nfse_nacional(self):
        """Scheduled action to poll SEFIN for status of sent NFS-e Nacional documents.

        Processes up to 25 documents in ENVIADA state that belong to the
        nfse_nacional provider, calling _document_status() on each.
        """
        records = (
            self.search([("state_edoc", "=", SITUACAO_EDOC_ENVIADA)], limit=25)
            .filtered(filter_processador_edoc_nfse)
            .filtered(filter_processador_nfse_nacional)
        )
        for record in records:
            record._document_status()
