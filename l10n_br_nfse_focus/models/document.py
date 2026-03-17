# Copyright 2023 - TODAY, KMEE INFORMATICA LTDA
# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Document model for FocusNFE NFSe integration."""

import base64
import logging
from datetime import datetime

import pytz
import requests

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

from .constants import (
    CODE_NFE_AUTORIZADA,
    CODE_NFE_CANCELADA,
    NFSE_URL,
    STATUS_AUTORIZADO,
    STATUS_CANCELADO,
    STATUS_ERRO_AUTORIZACAO,
    STATUS_PROCESSANDO_AUTORIZACAO,
    TIMEOUT,
)
from .helpers import (
    _is_valid_pdf,
    filter_focusnfe,
    filter_focusnfe_municipal,
    filter_focusnfe_nacional,
)

_logger = logging.getLogger(__name__)


class Document(models.Model):
    """Document model with FocusNFE NFSe integration."""

    _inherit = "l10n_br_fiscal.document"

    def make_focus_nfse_pdf(self, content):
        """Generate a PDF for a NFSe document using Focus NFSe service.

        Parameters:
            - content: The binary content of the PDF to be attached.

        Returns:
            None. Creates or updates an 'ir.attachment' record with the PDF content.
        """
        if not self.filtered(filter_processador_edoc_nfse).filtered(filter_focusnfe):
            return super().make_pdf()
        else:
            if self.document_number:
                filename = "NFS-e-" + self.document_number + ".pdf"
            else:
                filename = "RPS-" + self.rps_number + ".pdf"

            vals_dict = {
                "name": filename,
                "res_model": self._name,
                "res_id": self.id,
                "datas": base64.b64encode(content),
                "mimetype": "application/pdf",
                "type": "binary",
            }
            if self.file_report_id:
                self.file_report_id.write(vals_dict)
            else:
                self.file_report_id = self.env["ir.attachment"].create(vals_dict)

    def _serialize(self, edocs):
        """Serialize electronic documents (edocs) for sending to the NFSe provider.

        Parameters:
            - edocs: The initial list of electronic documents to serialize.

        Returns:
            The updated list of serialized electronic documents, including additional
            NFSe-specific information.
        """
        edocs = super()._serialize(edocs)
        # Handle NFSe Nacional
        for record in self.filtered(filter_processador_edoc_nfse).filtered(
            filter_focusnfe_nacional
        ):
            edoc = {
                "rps": record._prepare_lote_rps(),
                "service": record._prepare_dados_servico(),
                "recipient": record._prepare_dados_tomador(),
            }
            edocs.append(edoc)
        # Handle NFSe Municipal (original)
        for record in self.filtered(filter_processador_edoc_nfse).filtered(
            filter_focusnfe_municipal
        ):
            edoc = []
            edoc.append({"rps": record._prepare_lote_rps()})
            edoc.append({"service": record._prepare_dados_servico()})
            edoc.append({"recipient": record._prepare_dados_tomador()})
            edocs.append(edoc)
        return edocs

    def _document_export(self, pretty_print=True):
        """Prepare and export the document's electronic information.

        Parameters:
            - pretty_print: A boolean indicating whether the exported data should be
            formatted for readability.

        Returns:
            The result of the document export operation.
        """
        if self.filtered(filter_processador_edoc_nfse).filtered(filter_focusnfe):
            result = super(FiscalDocument, self)._document_export()
        else:
            result = super()._document_export()
        for record in self.filtered(filter_processador_edoc_nfse).filtered(
            filter_focusnfe
        ):
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

    def _parse_authorization_datetime(self, json_data):
        """Parse authorization datetime from JSON data.

        Args:
            json_data (dict): JSON response data.

        Returns:
            datetime: Naive datetime in UTC.
        """
        aware_datetime = datetime.strptime(
            json_data["data_emissao"], "%Y-%m-%dT%H:%M:%S%z"
        )
        utc_datetime = aware_datetime.astimezone(pytz.utc)
        return utc_datetime.replace(tzinfo=None)

    def _fetch_xml_from_path(self, record, xml_path):
        """Fetch XML content from the given path.

        Args:
            record: The document record.
            xml_path (str): Path to XML file.

        Returns:
            str: XML content as string, empty if path is invalid.
        """
        if not xml_path:
            return ""
        try:
            return requests.get(
                NFSE_URL[record.nfse_environment] + xml_path,
                timeout=TIMEOUT,
                verify=record.company_id.nfse_ssl_verify,
            ).content.decode("utf-8")
        except Exception as e:
            _logger.warning("Failed to fetch XML from %s: %s", xml_path, e)
            return ""

    def _fetch_pdf_from_urls(self, record, json_data, use_url_first=False):
        """Fetch PDF content from URLs in JSON data.

        Args:
            record: The document record.
            json_data (dict): JSON response data.
            use_url_first (bool): If True, try 'url' first, then 'url_danfse'.
                                 If False, only try 'url_danfse'.

        Returns:
            bytes: PDF content, or None if not found or invalid.
        """
        if record.company_id.focusnfe_nfse_force_odoo_danfse:
            return None

        pdf_url = None
        if use_url_first:
            pdf_url = json_data.get("url")
            if pdf_url:
                try:
                    pdf_content = requests.get(
                        pdf_url,
                        timeout=TIMEOUT,
                        verify=record.company_id.nfse_ssl_verify,
                    ).content
                    if _is_valid_pdf(pdf_content):
                        return pdf_content
                except Exception as e:
                    _logger.warning("Failed to fetch PDF from %s: %s", pdf_url, e)

        pdf_url = json_data.get("url_danfse", "")
        if pdf_url:
            try:
                pdf_content = requests.get(
                    pdf_url,
                    timeout=TIMEOUT,
                    verify=record.company_id.nfse_ssl_verify,
                ).content
                if _is_valid_pdf(pdf_content):
                    return pdf_content
            except Exception as e:
                _logger.warning("Failed to fetch PDF from %s: %s", pdf_url, e)

        return None

    def _process_authorized_status_base(
        self,
        record,
        json_data,
        verify_code_key="codigo_verificacao",
        use_url_first=False,
        xml_required=True,
    ):
        """Base method to process authorized status.

        Args:
            record: The document record.
            json_data (dict): JSON response data.
            verify_code_key (str): Key to get verification code from json_data.
            use_url_first (bool): Whether to try 'url' first for PDF.
            xml_required (bool): Whether XML path is required (municipal)
                or optional (nacional).
        """
        naive_datetime = self._parse_authorization_datetime(json_data)
        verify_code = (
            json_data.get(verify_code_key, "")
            if verify_code_key
            else json_data.get("codigo_verificacao", "")
        )
        document_number = json_data.get("numero", "")

        record.write(
            {
                "verify_code": verify_code,
                "document_number": document_number,
                "authorization_date": naive_datetime,
            }
        )

        xml_path = json_data.get("caminho_xml_nota_fiscal", "")
        if xml_required and not xml_path:
            # Will raise KeyError if not present
            xml_path = json_data.get("caminho_xml_nota_fiscal")

        xml = self._fetch_xml_from_path(record, xml_path) if xml_path else ""

        if not record.authorization_event_id:
            record._document_export()

        if record.authorization_event_id:
            # For municipal, xml is required; for nacional, only if available
            if xml_required or xml:
                record.authorization_event_id.set_done(
                    status_code=4,
                    response=_("Successfully Processed"),
                    protocol_date=record.authorization_date,
                    protocol_number=record.authorization_protocol,
                    file_response_xml=xml,
                )
                record._change_state(SITUACAO_EDOC_AUTORIZADA)

                if record.company_id.focusnfe_nfse_force_odoo_danfse:
                    record.make_pdf()
                else:
                    pdf_content = self._fetch_pdf_from_urls(
                        record, json_data, use_url_first
                    )
                    if pdf_content:
                        record.make_focus_nfse_pdf(pdf_content)

    def _process_authorized_status_nacional(self, record, json_data):
        """Process authorized status for NFSe Nacional."""
        self._process_authorized_status_base(
            record,
            json_data,
            verify_code_key="codigo_verificacao",
            use_url_first=False,
            xml_required=False,
        )

    def _process_authorized_status_municipal(self, record, json_data):
        """Process authorized status for NFSe Municipal."""
        self._process_authorized_status_base(
            record,
            json_data,
            verify_code_key="codigo_verificacao",
            use_url_first=True,
            xml_required=True,
        )

    def _process_error_status(self, record, json_data):
        """Process error authorization status."""
        erros = json_data.get("erros", [])
        error_msg = erros[0]["mensagem"] if erros else _("Authorization error")
        record.write(
            {
                "edoc_error_message": error_msg,
            }
        )
        record._change_state(SITUACAO_EDOC_REJEITADA)

    def _process_status_nacional(self, record):
        """Process status check for NFSe Nacional."""
        ref = str(record.rps_number)
        response = record.env[
            "focusnfe.nfse.nacional"
        ].query_focus_nfse_nacional_by_ref(
            ref, record.company_id, record.nfse_environment
        )

        json = response.json()

        edoc_states = ["a_enviar", "enviada", "rejeitada"]
        if record.company_id.focusnfe_nfse_update_authorized_document_status:
            edoc_states.append("autorizada")

        if response.status_code == 200:
            if record.state in edoc_states:
                if (
                    json["status"] == STATUS_AUTORIZADO
                    and record.state_edoc != SITUACAO_EDOC_AUTORIZADA
                ):
                    self._process_authorized_status_nacional(record, json)
                elif json["status"] == STATUS_ERRO_AUTORIZACAO:
                    self._process_error_status(record, json)
                elif json["status"] == STATUS_CANCELADO:
                    if record.state_edoc != SITUACAO_EDOC_CANCELADA:
                        record._document_cancel(record.cancel_reason)

            return _(json["status"])

        return "Unable to retrieve the document status."

    def _process_status_municipal(self, record):
        """Process status check for NFSe Municipal."""
        ref = "rps" + record.rps_number
        response = record.env["focusnfe.nfse"].query_focus_nfse_by_rps(
            ref, 0, record.company_id, record.nfse_environment
        )

        json = response.json()

        edoc_states = ["a_enviar", "enviada", "rejeitada"]
        if record.company_id.focusnfe_nfse_update_authorized_document_status:
            edoc_states.append("autorizada")

        if response.status_code == 200:
            if record.state in edoc_states:
                if (
                    json["status"] == STATUS_AUTORIZADO
                    and record.state_edoc != SITUACAO_EDOC_AUTORIZADA
                ):
                    self._process_authorized_status_municipal(record, json)
                elif json["status"] == STATUS_ERRO_AUTORIZACAO:
                    record.write(
                        {
                            "edoc_error_message": json["erros"][0]["mensagem"],
                        }
                    )
                    record._change_state(SITUACAO_EDOC_REJEITADA)
                elif json["status"] == STATUS_CANCELADO:
                    if record.state_edoc != SITUACAO_EDOC_CANCELADA:
                        record._document_cancel(record.cancel_reason)

            return _(json["status"])

        return "Unable to retrieve the document status."

    def _document_status(self):
        """Check and update the status of the NFSe document.

        Parameters:
            None.

        Returns:
            A string indicating the current status of the document.
        """
        result = super()._document_status()
        # Handle NFSe Nacional
        for record in self.filtered(filter_processador_edoc_nfse).filtered(
            filter_focusnfe_nacional
        ):
            result = self._process_status_nacional(record)
        # Handle NFSe Municipal (original)
        for record in self.filtered(filter_processador_edoc_nfse).filtered(
            filter_focusnfe_municipal
        ):
            result = self._process_status_municipal(record)

        return result

    def create_cancel_event(self, status_json, record):
        """Create a cancel event and process it.

        Parameters:
            record: The NFSe record that is being canceled.

        Returns:
            The created event.
        """
        xml_path = status_json.get("caminho_xml_cancelamento", "")
        xml = ""
        if xml_path:
            xml = requests.get(
                NFSE_URL[record.nfse_environment] + xml_path,
                timeout=TIMEOUT,
                verify=record.company_id.nfse_ssl_verify,
            ).content.decode("utf-8")

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
            file_response_xml=xml,
        )
        return event

    def fetch_and_verify_pdf_content(self, status_json, record):
        """Fetch and verify the PDF content from the provided URL.

        Parameters:
            status_json: JSON response containing the URLs for the PDF.
            record: The NFSe record for which the PDF is being retrieved.

        Returns:
            None. Updates the record with the PDF content if valid.
        """
        pdf_content = requests.get(
            status_json["url"],
            timeout=TIMEOUT,
            verify=record.company_id.nfse_ssl_verify,
        ).content
        if not _is_valid_pdf(pdf_content):
            pdf_content = requests.get(
                status_json["url_danfse"],
                timeout=TIMEOUT,
                verify=record.company_id.nfse_ssl_verify,
            ).content
        if _is_valid_pdf(pdf_content):
            record.make_focus_nfse_pdf(pdf_content)

    def _handle_cancelled_status(self, record, status_json, use_url_first=False):
        """Handle already cancelled status.

        Args:
            record: The document record.
            status_json (dict): Status JSON response.
            use_url_first (bool): Whether to try 'url' first for PDF.
        """
        record.cancel_event_id = record.create_cancel_event(status_json, record)
        if record.company_id.focusnfe_nfse_force_odoo_danfse:
            record.make_pdf()
        else:
            if use_url_first:
                record.fetch_and_verify_pdf_content(status_json, record)
            else:
                url_danfse = status_json.get("url_danfse", "")
                if url_danfse:
                    pdf_content = requests.get(
                        url_danfse,
                        timeout=TIMEOUT,
                        verify=record.company_id.nfse_ssl_verify,
                    ).content
                    if _is_valid_pdf(pdf_content):
                        record.make_focus_nfse_pdf(pdf_content)

    def _process_cancel_base(
        self,
        record,
        ref,
        query_method,
        cancel_method,
        use_url_first=False,
        apply_barueri_hack=False,
    ):
        """Base method to process cancellation.

        Args:
            record: The document record.
            ref (str): Document reference.
            query_method: Method to query document status.
            cancel_method: Method to cancel document.
            use_url_first (bool): Whether to try 'url' first for PDF.
            apply_barueri_hack (bool): Whether to apply Barueri-specific hack.

        Returns:
            requests.Response: The cancellation response.
        """
        # Check current status
        status_response = query_method(ref, record.company_id, record.nfse_environment)
        status_json = status_response.json()

        if status_response.status_code == 200:
            status = (
                status_json.get("status", "")
                if isinstance(status_json, dict)
                else status_json.get("status", "")
            )
            if (
                status == STATUS_CANCELADO
                and record.state_edoc != SITUACAO_EDOC_CANCELADA
            ):
                self._handle_cancelled_status(record, status_json, use_url_first)
                return status_response

        # Perform cancellation
        response = cancel_method(
            ref, record.cancel_reason, record.company_id, record.nfse_environment
        )
        json_data = response.json()

        if response.status_code in [200, 400]:
            code = json_data.get("codigo", "")
            status = json_data.get("status", "")

            if not code:
                code = json_data.get("erros", [{}])[0].get("codigo", "")
                if code == "OK200" or (not code and status == STATUS_CANCELADO):
                    code = CODE_NFE_CANCELADA

            if code == CODE_NFE_CANCELADA or status == STATUS_CANCELADO:
                # Query status again after cancellation
                status_rps = query_method(
                    ref, record.company_id, record.nfse_environment
                )
                status_json = status_rps.json()
                self._handle_cancelled_status(record, status_json, use_url_first)
                return response

            raise UserError(
                _(
                    "%(code)s - %(status)s",
                    code=code or response.status_code,
                    status=status,
                )
            )

        raise UserError(
            _(
                "%(code)s - %(msg)s",
                code=response.status_code,
                msg=json_data.get("mensagem", ""),
            )
        )

    def _process_cancel_nacional(self, record):
        """Process cancellation for NFSe Nacional."""
        ref = str(record.rps_number)
        nfse_nacional = record.env["focusnfe.nfse.nacional"]

        def query_method(ref, company, environment):
            return nfse_nacional.query_focus_nfse_nacional_by_ref(
                ref, company, environment
            )

        def cancel_method(ref, cancel_reason, company, environment):
            return nfse_nacional.cancel_focus_nfse_nacional_document(
                ref, cancel_reason, company, environment
            )

        return self._process_cancel_base(
            record, ref, query_method, cancel_method, use_url_first=False
        )

    def _process_cancel_municipal(self, record):
        """Process cancellation for NFSe Municipal."""
        ref = "rps" + record.rps_number
        nfse = record.env["focusnfe.nfse"]

        def query_method(ref, company, environment):
            return nfse.query_focus_nfse_by_rps(ref, 0, company, environment)

        def cancel_method(ref, cancel_reason, company, environment):
            return nfse.cancel_focus_nfse_document(
                ref, cancel_reason, company, environment
            )

        return self._process_cancel_base(
            record,
            ref,
            query_method,
            cancel_method,
            use_url_first=True,
            apply_barueri_hack=True,
        )

    def cancel_document_focus(self):
        """Cancel a NFSe document with the Focus NFSe provider.

        Parameters:
            None.

        Returns:
            The response regarding the cancellation request.
        """
        # Handle NFSe Nacional
        for record in self.filtered(filter_processador_edoc_nfse).filtered(
            filter_focusnfe_nacional
        ):
            return self._process_cancel_nacional(record)
        # Handle NFSe Municipal (original)
        for record in self.filtered(filter_processador_edoc_nfse).filtered(
            filter_focusnfe_municipal
        ):
            return self._process_cancel_municipal(record)

    def _process_send_nacional(self, record):
        """Process document send for NFSe Nacional."""
        for edoc in record.serialize():
            ref = str(record.rps_number)
            response = self.env[
                "focusnfe.nfse.nacional"
            ].process_focus_nfse_nacional_document(
                edoc, ref, record.company_id, record.nfse_environment
            )
            json = response.json()

            if response.status_code == 202:
                if json["status"] == STATUS_PROCESSANDO_AUTORIZACAO:
                    if record.state == "rejeitada":
                        record.state_edoc = SITUACAO_EDOC_ENVIADA
                    else:
                        record._change_state(SITUACAO_EDOC_ENVIADA)
            elif response.status_code == 422:
                code = json.get("codigo", "")
                if code == CODE_NFE_AUTORIZADA and record.state in [
                    "a_enviar",
                    "enviada",
                    "rejeitada",
                ]:
                    record._document_status()
                else:
                    record._change_state(SITUACAO_EDOC_REJEITADA)
            else:
                record._change_state(SITUACAO_EDOC_REJEITADA)

    def _process_send_municipal(self, record):
        """Process document send for NFSe Municipal."""
        for edoc in record.serialize():
            ref = "rps" + record.rps_number
            response = self.env["focusnfe.nfse"].process_focus_nfse_document(
                edoc, ref, record.company_id, record.nfse_environment
            )
            json = response.json()

            if response.status_code == 202:
                if json["status"] == STATUS_PROCESSANDO_AUTORIZACAO:
                    if record.state == "rejeitada":
                        record.state_edoc = SITUACAO_EDOC_ENVIADA
                    else:
                        record._change_state(SITUACAO_EDOC_ENVIADA)
            elif response.status_code == 422:
                code = json.get("codigo", "")
                if code == CODE_NFE_AUTORIZADA and record.state in [
                    "a_enviar",
                    "enviada",
                    "rejeitada",
                ]:
                    record._document_status()
                else:
                    record._change_state(SITUACAO_EDOC_REJEITADA)
            else:
                record._change_state(SITUACAO_EDOC_REJEITADA)

    def _eletronic_document_send(self):
        """Send the electronic document to the NFSe provider.

        Parameters:
            None.

        Returns:
            None. Updates the document's status based on the response.
        """
        res = super()._eletronic_document_send()
        # Handle NFSe Nacional
        for record in self.filtered(filter_processador_edoc_nfse).filtered(
            filter_focusnfe_nacional
        ):
            self._process_send_nacional(record)
        # Handle NFSe Municipal (original)
        for record in self.filtered(filter_processador_edoc_nfse).filtered(
            filter_focusnfe_municipal
        ):
            self._process_send_municipal(record)
        return res

    def _exec_before_SITUACAO_EDOC_CANCELADA(self, old_state, new_state):
        """Hook method before changing document's state to 'Cancelled'.

        Parameters:
            - old_state: The document's previous state.
            - new_state: The new state.

        Returns:
            The result of the cancellation process.
        """
        super()._exec_before_SITUACAO_EDOC_CANCELADA(old_state, new_state)
        return self.cancel_document_focus()

    @api.model
    def _cron_document_status_focus(self):
        """Scheduled method to check the status of sent NFSe documents.

        Parameters:
            None.

        Returns:
            None. Updates the status of each document based on the NFSe provider's
            response.
        """
        records = (
            self.search([("state", "in", ["enviada"])], limit=25)
            .filtered(filter_processador_edoc_nfse)
            .filtered(filter_focusnfe)
        )
        # Iterate over each record individually, as _document_status()
        # may expect a singleton in some cases
        for record in records:
            record._document_status()
