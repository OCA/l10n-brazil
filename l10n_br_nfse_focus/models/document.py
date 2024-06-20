# Copyright 2023 - TODAY, KMEE INFORMATICA LTDA
# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import json
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

NFSE_URL = {
    "1": "https://api.focusnfe.com.br",
    "2": "https://homologacao.focusnfe.com.br",
}

API_ENDPOINT = {
    "envio": "/v2/nfse?",
    "status": "/v2/nfse/",
    "resposta": "/v2/nfse/",
    "cancelamento": "/v2/nfse/",
}

TIMEOUT = 60  # 60 seconds

_logger = logging.getLogger(__name__)


def filter_focusnfe(record):
    return record.company_id.provedor_nfse == "focusnfe"


class FocusnfeNfse(models.AbstractModel):
    _name = "focusnfe.nfse"
    _description = "FocusNFE NFSE"

    def _make_focus_nfse_http_request(self, method, url, token, data=None, params=None):
        """Perform a generic HTTP request.

        Args:
            method (str): The HTTP method to use (e.g., 'GET', 'POST').
            url (str): The URL to which the request is sent.
            token (str): The authentication token for the service.
            data (dict, optional): The payload to send in the request body.
                Defaults to None.
            params (dict, optional): The URL parameters to append to the URL.
                Defaults to None.

        Returns:
            requests.Response: The response object from the requests library.

        Raises:
            UserError: If the HTTP request fails with a 4xx/5xx response.
        """
        auth = (token, "")
        try:
            response = requests.request(  # pylint: disable=external-request-timeout
                method,
                url,
                data=data,
                params=params,
                auth=auth,
            )
            response.raise_for_status()  # Raises an error for 4xx/5xx responses
            return response
        except requests.HTTPError as e:
            raise UserError(_("Error communicating with NFSe service: %s") % e) from e

    def _identify_service_recipient(self, recipient):
        """Identify whether the service recipient is a CPF or CNPJ.

        Args:
            recipient (dict): A dictionary containing either 'cpf' or 'cnpj' keys.

        Returns:
            dict: A dictionary with either a 'cpf' or 'cnpj' key and its value.
        """
        return (
            {"cpf": recipient.get("cpf")}
            if recipient.get("cpf")
            else {"cnpj": recipient.get("cnpj")}
        )

    @api.model
    def process_focus_nfse_document(self, edoc, ref, company, environment):
        """Process the electronic fiscal document.

        Args:
            edoc (tuple): The electronic document data.
            ref (str): The document reference.
            company (recordset): The company record.

        Returns:
            requests.Response: The response from the NFSe service.
        """
        token = company.get_focusnfe_token()
        data = self._prepare_payload(*edoc, company)
        payload = json.dumps(data)
        url = f"{NFSE_URL[environment]}{API_ENDPOINT['envio']}"
        ref = {"ref": ref}
        return self._make_focus_nfse_http_request(
            "POST", url, token, data=payload, params=ref
        )

    def _prepare_payload(self, rps, service, recipient, company):
        """Construct the NFSe payload.

        Args:
            rps (dict): Information about the RPS.
            service (dict): Details of the service provided.
            recipient (dict): Information about the service recipient.
            company (recordset): The company record.

        Returns:
            dict: The complete payload for the NFSe request.
        """
        rps_info = rps.get("rps")
        service_info = service.get("service")
        recipient_info = recipient.get("recipient")
        recipient_identification = self._identify_service_recipient(recipient_info)
        return {
            "prestador": self._prepare_provider_data(rps_info, company),
            "servico": self._prepare_service_data(service_info, company),
            "tomador": self._prepare_recipient_data(
                recipient_info, recipient_identification
            ),
            "razao_social": company.name,
            "data_emissao": rps_info.get("data_emissao"),
            "incentivador_cultural": rps_info.get("incentivador_cultural", False),
            "natureza_operacao": rps_info.get("natureza_operacao"),
            "optante_simples_nacional": rps_info.get("optante_simples_nacional", False),
            "status": rps_info.get("status"),
            "codigo_obra": rps_info.get("codigo_obra", ""),
            "art": rps_info.get("art", ""),
        }

    def _prepare_provider_data(self, rps, company):
        """Construct the provider section of the payload.

        Args:
            rps (dict): Information about the RPS.
            company (recordset): The company record.

        Returns:
            dict: The provider section of the payload.
        """
        return {
            "cnpj": rps.get("cnpj"),
            "inscricao_municipal": rps.get("inscricao_municipal"),
            "codigo_municipio": company.city_id.ibge_code,
        }

    def _prepare_service_data(self, service, company):
        """Construct the service section of the payload.

        Args:
            service (dict): Details of the service provided.
            company (recordset): The company record.

        Returns:
            dict: The service section of the payload.
        """
        return {
            "aliquota": service.get("aliquota"),
            "base_calculo": round(service.get("base_calculo", 0), 2),
            "discriminacao": service.get("discriminacao"),
            "iss_retido": service.get("iss_retido"),
            "codigo_municipio": service.get("municipio_prestacao_servico"),
            "item_lista_servico": service.get(company.focusnfe_nfse_service_type_value),
            "codigo_cnae": service.get(company.focusnfe_nfse_cnae_code_value),
            "valor_iss": round(service.get("valor_iss", 0), 2),
            "valor_iss_retido": round(service.get("valor_iss_retido", 0), 2),
            "valor_pis": round(service.get("valor_pis", 0), 2),
            "valor_cofins": round(service.get("valor_cofins", 0), 2),
            "valor_inss": round(service.get("valor_inss", 0), 2),
            "valor_ir": round(service.get("valor_ir", 0), 2),
            "valor_csll": round(service.get("valor_csll", 0), 2),
            "valor_deducoes": round(service.get("valor_deducoes", 0), 2),
            "fonte_total_tributos": service.get("fonte_total_tributos", "IBPT"),
            "desconto_incondicionado": round(
                service.get("desconto_incondicionado", 0), 2
            ),
            "desconto_condicionado": round(service.get("desconto_condicionado", 0), 2),
            "outras_retencoes": round(service.get("outras_retencoes", 0), 2),
            "valor_servicos": round(service.get("valor_servicos", 0), 2),
            "valor_liquido": round(service.get("valor_liquido_nfse", 0), 2),
            "codigo_tributario_municipio": service.get("codigo_tributacao_municipio"),
        }

    def _prepare_recipient_data(self, recipient, identification):
        """Construct the recipient section of the payload.

        Args:
            recipient (dict): Information about the service recipient.
            identification (dict): The recipient's identification (CPF or CNPJ).

        Returns:
            dict: The recipient section of the payload.
        """
        return {
            **identification,
            "razao_social": recipient.get("razao_social"),
            "email": recipient.get("email"),
            "endereco": {
                "bairro": recipient.get("bairro"),
                "cep": recipient.get("cep"),
                "codigo_municipio": recipient.get("codigo_municipio"),
                "logradouro": recipient.get("endereco"),
                "numero": recipient.get("numero"),
                "uf": recipient.get("uf"),
            },
        }

    @api.model
    def query_focus_nfse_by_rps(self, ref, complete, company, environment):
        """Query NFSe by RPS.

        Args:
            ref (str): The RPS reference.
            complete (bool): Whether to return complete information.
            company (recordset): The company record.

        Returns:
            requests.Response: The response from the NFSe service.
        """
        token = company.get_focusnfe_token()
        url = f"{NFSE_URL[environment]}{API_ENDPOINT['status']}{ref}"
        return self._make_focus_nfse_http_request(
            "GET", url, token, params={"completa": complete}
        )

    @api.model
    def cancel_focus_nfse_document(self, ref, cancel_reason, company, environment):
        """Cancel an electronic fiscal document.

        Args:
            ref (str): The document reference.
            cancel_reason (str): The reason for cancellation.
            company (recordset): The company record.

        Returns:
            requests.Response: The response from the NFSe service.
        """
        token = company.get_focusnfe_token()
        data = {"justificativa": cancel_reason}
        url = f"{NFSE_URL[environment]}{API_ENDPOINT['cancelamento']}{ref}"
        return self._make_focus_nfse_http_request(
            "DELETE", url, token, data=json.dumps(data)
        )


class Document(models.Model):
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
        for record in self.filtered(filter_processador_edoc_nfse).filtered(
            filter_focusnfe
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
                company_id=self.company_id,
                environment=(
                    EVENT_ENV_PROD if record.nfse_environment == "1" else EVENT_ENV_HML
                ),
                event_type="0",
                xml_file="",
                document_id=record,
            )
            record.authorization_event_id = event_id
        return result

    def _document_status(self):
        """Check and update the status of the NFSe document.

        Parameters:
            None.

        Returns:
            A string indicating the current status of the document.
        """
        result = super()._document_status()
        for record in self.filtered(filter_processador_edoc_nfse).filtered(
            filter_focusnfe
        ):
            ref = "rps" + record.rps_number
            response = self.env["focusnfe.nfse"].query_focus_nfse_by_rps(
                ref, 0, record.company_id, record.nfse_environment
            )

            json = response.json()

            if response.status_code == 200:
                if record.state in ["a_enviar", "enviada", "rejeitada"]:
                    if json["status"] == "autorizado":
                        aware_datetime = datetime.strptime(
                            json["data_emissao"], "%Y-%m-%dT%H:%M:%S%z"
                        )
                        utc_datetime = aware_datetime.astimezone(pytz.utc)
                        naive_datetime = utc_datetime.replace(tzinfo=None)
                        record.write(
                            {
                                "verify_code": json["codigo_verificacao"],
                                "document_number": json["numero"],
                                "authorization_date": naive_datetime,
                            }
                        )

                        xml = requests.get(
                            NFSE_URL[record.nfse_environment]
                            + json["caminho_xml_nota_fiscal"],
                            timeout=TIMEOUT,
                        ).content.decode("utf-8")
                        pdf_content = (
                            requests.get(
                                json["url"],
                                timeout=TIMEOUT,
                                verify=record.company_id.nfse_ssl_verify,
                            ).content
                            or requests.get(
                                json["url_danfse"],
                                timeout=TIMEOUT,
                                verify=record.company_id.nfse_ssl_verify,
                            ).content
                        )

                        record.make_focus_nfse_pdf(pdf_content)

                        if not record.authorization_event_id:
                            record._document_export()

                        if record.authorization_event_id:
                            record.authorization_event_id.set_done(
                                status_code=4,
                                response=_("Processado com Sucesso"),
                                protocol_date=record.authorization_date,
                                protocol_number=record.authorization_protocol,
                                file_response_xml=xml,
                            )
                            record._change_state(SITUACAO_EDOC_AUTORIZADA)

                    elif json["status"] == "erro_autorizacao":
                        record.write(
                            {
                                "edoc_error_message": json["erros"][0]["mensagem"],
                            }
                        )
                        record._change_state(SITUACAO_EDOC_REJEITADA)
                    elif json["status"] == "cancelado":
                        record._change_state(SITUACAO_EDOC_CANCELADA)

                result = _(json["status"])
            else:
                result = "Unable to retrieve the document status."
        return result

    def cancel_document_focus(self):
        """Cancel a NFSe document with the Focus NFSe provider.

        Parameters:
            None.

        Returns:
            The response regarding the cancellation request.
        """
        for record in self.filtered(filter_processador_edoc_nfse).filtered(
            filter_focusnfe
        ):
            ref = "rps" + record.rps_number
            response = self.env["focusnfe.nfse"].cancel_focus_nfse_document(
                ref, record.cancel_reason, record.company_id, record.nfse_environment
            )

            code = False
            status = False

            json = response.json()

            if response.status_code in [200, 400]:
                try:
                    code = json["codigo"]
                    response = True
                except Exception:
                    _logger.error(
                        _("HTTP status is 200 or 400 but unable to read json['codigo']")
                    )
                try:
                    status = json["status"]
                except Exception:
                    _logger.error(
                        _("HTTP status is 200 or 400 but unable to read json['status']")
                    )

                # hack barueri - provisório
                if not code and record.company_id.city_id.ibge_code == "3505708":
                    try:
                        code = json["erros"][0].get("codigo")
                    except Exception:
                        _logger.error(
                            _("HTTP status is 200 or 400 but unable to read error code")
                        )
                    if code == "OK200":
                        code = "nfe_cancelada"

                if code == "nfe_cancelada" or status == "cancelado":
                    record.cancel_event_id = record.event_ids.create_event_save_xml(
                        company_id=record.company_id,
                        environment=(
                            EVENT_ENV_PROD
                            if record.nfse_environment == "1"
                            else EVENT_ENV_HML
                        ),
                        event_type="2",
                        xml_file="",
                        document_id=record,
                    )

                    record.cancel_event_id.set_done(
                        status_code=4,
                        response=_("Processado com Sucesso"),
                        protocol_date=fields.Datetime.to_string(fields.Datetime.now()),
                        protocol_number="",
                        file_response_xml="",
                    )

                    status_rps = self.env["focusnfe.nfse"].query_focus_nfse_by_rps(
                        ref, 0, record.company_id, record.nfse_environment
                    )
                    status_json = status_rps.json()
                    pdf_content = (
                        requests.get(
                            status_json["url"],
                            timeout=TIMEOUT,
                            verify=record.company_id.nfse_ssl_verify,
                        ).content
                        or requests.get(
                            status_json["url_danfse"],
                            timeout=TIMEOUT,
                            verify=record.company_id.nfse_ssl_verify,
                        ).content
                    )
                    record.make_focus_nfse_pdf(pdf_content)

                    return response

                else:
                    raise UserError(
                        _(
                            "%(code)s - %(status)s",
                            code=response.status_code,
                            status=status,
                        )
                    )
            else:
                raise UserError(
                    _(
                        "%(code)s - %(msg)s",
                        code=response.status_code,
                        msg=json["mensagem"],
                    )
                )

    def _eletronic_document_send(self):
        """Send the electronic document to the NFSe provider.

        Parameters:
            None.

        Returns:
            None. Updates the document's status based on the response.
        """
        res = super()._eletronic_document_send()
        for record in self.filtered(filter_processador_edoc_nfse).filtered(
            filter_focusnfe
        ):
            for edoc in record.serialize():
                ref = "rps" + record.rps_number
                response = self.env["focusnfe.nfse"].process_focus_nfse_document(
                    edoc, ref, record.company_id, record.nfse_environment
                )
                json = response.json()

                if response.status_code == 202:
                    if json["status"] == "processando_autorizacao":
                        if record.state == "rejeitada":
                            record.state_edoc = SITUACAO_EDOC_ENVIADA
                        else:
                            record._change_state(SITUACAO_EDOC_ENVIADA)
                elif response.status_code == 422:
                    try:
                        code = json["codigo"]
                    except Exception:
                        code = ""

                    if code == "nfe_autorizada" and record.state in [
                        "a_enviar",
                        "enviada",
                        "rejeitada",
                    ]:
                        record._document_status()
                    else:
                        record._change_state(SITUACAO_EDOC_REJEITADA)
                else:
                    record._change_state(SITUACAO_EDOC_REJEITADA)
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
        if records:
            records._document_status()
