# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""NFSe Nacional integration with FocusNFE."""

import json

from odoo import api

from .base import FocusnfeNfseBase
from .constants import API_ENDPOINT_NACIONAL, NFSE_URL
from .helpers import _identify_cpf_cnpj


class FocusnfeNfseNacional(FocusnfeNfseBase):
    """FocusNFE NFSe Nacional implementation."""

    _name = "focusnfe.nfse.nacional"
    _description = "FocusNFE NFSe Nacional"

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
        return super()._make_focus_nfse_http_request(
            method, url, token, data, params, service_name="NFSe Nacional"
        )

    @api.model
    def process_focus_nfse_nacional_document(self, edoc, ref, company, environment):
        """Process the electronic fiscal document for NFSe Nacional.

        Args:
            edoc (dict): The electronic document data.
            ref (str): The document reference.
            company (recordset): The company record.
            environment (str): The environment (1=production, 2=homologation).

        Returns:
            requests.Response: The response from the NFSe Nacional service.
        """
        token = company.get_focusnfe_token()
        data = self._prepare_payload_nacional(edoc, company)
        payload = json.dumps(data)
        url = f"{NFSE_URL[environment]}{API_ENDPOINT_NACIONAL['envio']}"
        ref_params = {"ref": ref}
        return self._make_focus_nfse_http_request(
            "POST", url, token, data=payload, params=ref_params
        )

    def _prepare_dates_nacional(self, rps_info):
        """Prepare emission and competence dates for NFSe Nacional.

        Args:
            rps_info (dict): RPS information.

        Returns:
            tuple: (emission_date, competence_date)
        """
        emission_date = rps_info.get("data_emissao", "")
        if emission_date and not emission_date.endswith(("-0300", "-0200", "+0000")):
            # Add timezone if not present (assuming -0300 for Brazil)
            emission_date = emission_date + "-0300"

        competence_date = (
            rps_info.get("data_emissao", "")[:10]
            if rps_info.get("data_emissao")
            else ""
        )

        return emission_date, competence_date

    def _prepare_provider_nacional(self, rps_info, company):
        """Prepare provider data for NFSe Nacional.

        Args:
            rps_info (dict): RPS information.
            company (recordset): The company record.

        Returns:
            dict: Provider data with CPF/CNPJ identification.
        """
        cnpj_prestador = rps_info.get("cnpj", "")
        cpf_prestador = rps_info.get("cpf", "")
        (
            is_cpf_prestador,
            is_cnpj_prestador,
            cpf_prestador_limpo,
            cnpj_prestador_limpo,
        ) = _identify_cpf_cnpj(cpf_prestador, cnpj_prestador)

        optante_simples = rps_info.get("optante_simples_nacional", "1")
        codigo_opcao_simples_nacional = "2" if optante_simples == "1" else "1"

        regime_especial_tributacao = (
            rps_info.get("regime_especial_tributacao", "0") or "0"
        )

        return {
            "is_cpf": is_cpf_prestador,
            "is_cnpj": is_cnpj_prestador,
            "cpf_limpo": cpf_prestador_limpo,
            "cnpj_limpo": cnpj_prestador_limpo,
            "codigo_opcao_simples_nacional": codigo_opcao_simples_nacional,
            "regime_especial_tributacao": regime_especial_tributacao,
            "codigo_municipio_emissora": str(company.city_id.ibge_code or ""),
        }

    def _prepare_recipient_nacional(self, recipient_info):
        """Prepare recipient data for NFSe Nacional.

        Args:
            recipient_info (dict): Recipient information.

        Returns:
            dict: Recipient data with CPF/CNPJ identification.
        """
        cnpj_tomador = recipient_info.get("cnpj", "")
        cpf_tomador = recipient_info.get("cpf", "")
        is_cpf, is_cnpj, cpf_limpo, cnpj_limpo = _identify_cpf_cnpj(
            cpf_tomador, cnpj_tomador
        )

        cep_tomador = recipient_info.get("cep", "")
        if isinstance(cep_tomador, int):
            cep_tomador = str(cep_tomador)

        return {
            "is_cpf": is_cpf,
            "is_cnpj": is_cnpj,
            "cpf_limpo": cpf_limpo,
            "cnpj_limpo": cnpj_limpo,
            "razao_social": recipient_info.get("razao_social", ""),
            "codigo_municipio": str(recipient_info.get("codigo_municipio", "")),
            "cep": cep_tomador or "",
            "logradouro": recipient_info.get("endereco", ""),
            "numero": recipient_info.get("numero", ""),
            "complemento": recipient_info.get("complemento", ""),
            "bairro": recipient_info.get("bairro", ""),
            "telefone": recipient_info.get("telefone", ""),
            "email": recipient_info.get("email", ""),
        }

    def _prepare_service_basic_nacional(self, service_info):
        """Prepare basic service data for NFSe Nacional.

        Args:
            service_info (dict): Service information.

        Returns:
            dict: Basic service data.
        """
        codigo_municipio_prestacao = service_info.get("municipio_prestacao_servico", "")

        codigo_tributacao_nacional = service_info.get("codigo_tributacao_nacional", "")

        codigo_tributacao_municipio = service_info.get(
            "codigo_tributacao_municipio", ""
        )

        tributacao_iss = service_info.get("codigo_tributacao_iss", "")

        # TODO: improve logic to get ISS retention code
        tipo_retencao_iss = "2" if service_info.get("iss_retido") == "1" else "1"

        return {
            "codigo_municipio_prestacao": str(codigo_municipio_prestacao),
            "codigo_tributacao_nacional": codigo_tributacao_nacional,
            "codigo_tributacao_municipio": codigo_tributacao_municipio,
            "descricao": service_info.get("discriminacao", ""),
            "valor": round(service_info.get("valor_servicos", 0), 2),
            "tributacao_iss": str(tributacao_iss),
            "tipo_retencao_iss": str(tipo_retencao_iss),
        }

    def _prepare_tax_data_nacional(self, service_info, valor_servico):
        """Prepare tax data (PIS/COFINS, etc.) for NFSe Nacional.

        Args:
            service_info (dict): Service information.
            valor_servico (float): Service value.

        Returns:
            dict: Tax data.
        """
        # PIS/COFINS tax situation
        situacao_tributaria_pis_cofins = (
            service_info.get("situacao_tributaria_pis", "")
            or service_info.get("situacao_tributaria_cofins", "")
            or ""
        )
        if situacao_tributaria_pis_cofins == "99":
            situacao_tributaria_pis_cofins = "00"

        # PIS/COFINS calculation base
        base_calculo_pis = service_info.get("base_calculo_pis", 0)
        base_calculo_cofins = service_info.get("base_calculo_cofins", 0)
        base_calculo_pis_cofins = round(
            base_calculo_pis if base_calculo_pis else base_calculo_cofins, 2
        )

        if situacao_tributaria_pis_cofins:
            if situacao_tributaria_pis_cofins in ["00", "08", "09"]:
                base_calculo_pis_cofins = 0.0
            else:
                if not base_calculo_pis_cofins or base_calculo_pis_cofins == 0:
                    base_calculo_pis_cofins = round(valor_servico, 2)

        # Format rates as strings with 2 decimal places
        aliquota_pis_raw = round(service_info.get("aliquota_pis", 0), 2)
        aliquota_pis = f"{aliquota_pis_raw:.2f}"
        aliquota_cofins_raw = round(service_info.get("aliquota_cofins", 0), 2)
        aliquota_cofins = f"{aliquota_cofins_raw:.2f}"

        return {
            "situacao_tributaria_pis_cofins": situacao_tributaria_pis_cofins or "",
            "base_calculo_pis_cofins": round(base_calculo_pis_cofins, 2),
            "aliquota_pis": aliquota_pis,
            "aliquota_cofins": aliquota_cofins,
            "valor_pis": round(service_info.get("valor_pis", 0), 2),
            "valor_cofins": round(service_info.get("valor_cofins", 0), 2),
            "tipo_retencao_pis_cofins": service_info.get(
                "tipo_retencao_pis_cofins", "2"
            ),
            "valor_cp": round(service_info.get("valor_inss_retido", 0), 2),
            "valor_irrf": round(service_info.get("valor_ir_retido", 0), 2),
            "valor_csll": round(service_info.get("valor_csll_retido", 0), 2),
        }

    def _prepare_payload_nacional(self, edoc, company):
        """Construct the NFSe Nacional payload.

        Args:
            edoc (dict): The electronic document data containing rps,
                service, recipient.
            company (recordset): The company record.

        Returns:
            dict: The complete payload for the NFSe Nacional request.
        """
        rps_info = edoc.get("rps", {})
        service_info = edoc.get("service", {})
        recipient_info = edoc.get("recipient", {})

        # Prepare dates
        emission_date, competence_date = self._prepare_dates_nacional(rps_info)

        # Prepare provider data
        provider_data = self._prepare_provider_nacional(rps_info, company)

        # Prepare recipient data
        recipient_data = self._prepare_recipient_nacional(recipient_info)

        # Prepare service data
        service_basic = self._prepare_service_basic_nacional(service_info)
        tax_data = self._prepare_tax_data_nacional(service_info, service_basic["valor"])

        # Build payload
        payload = {
            "data_emissao": emission_date,
            "data_competencia": competence_date,
            "codigo_municipio_emissora": provider_data["codigo_municipio_emissora"],
            **(
                {"cnpj_prestador": provider_data["cnpj_limpo"]}
                if provider_data["is_cnpj"]
                else {}
            ),
            **(
                {"cpf_prestador": provider_data["cpf_limpo"]}
                if provider_data["is_cpf"]
                else {}
            ),
            "codigo_opcao_simples_nacional": provider_data[
                "codigo_opcao_simples_nacional"
            ],
            "regime_especial_tributacao": provider_data["regime_especial_tributacao"],
            **(
                {"cnpj_tomador": recipient_data["cnpj_limpo"]}
                if recipient_data["is_cnpj"]
                else {}
            ),
            **(
                {"cpf_tomador": recipient_data["cpf_limpo"]}
                if recipient_data["is_cpf"]
                else {}
            ),
            "razao_social_tomador": recipient_data["razao_social"],
            "codigo_municipio_tomador": recipient_data["codigo_municipio"],
            "cep_tomador": recipient_data["cep"],
            "logradouro_tomador": recipient_data["logradouro"],
            "numero_tomador": recipient_data["numero"],
            "complemento_tomador": recipient_data["complemento"],
            "bairro_tomador": recipient_data["bairro"],
            "telefone_tomador": recipient_data["telefone"],
            "email_tomador": recipient_data["email"],
            "codigo_municipio_prestacao": service_basic["codigo_municipio_prestacao"],
            "codigo_tributacao_nacional_iss": service_basic[
                "codigo_tributacao_nacional"
            ],
            "codigo_tributacao_municipal_iss": service_basic[
                "codigo_tributacao_municipio"
            ],
            "descricao_servico": service_basic["descricao"],
            "valor_servico": service_basic["valor"],
            "tributacao_iss": service_basic["tributacao_iss"],
            "tipo_retencao_iss": service_basic["tipo_retencao_iss"],
            **tax_data,
        }

        return payload

    @api.model
    def query_focus_nfse_nacional_by_ref(self, ref, company, environment):
        """Query NFSe Nacional by reference.

        Args:
            ref (str): The document reference.
            company (recordset): The company record.
            environment (str): The environment (1=production, 2=homologation).

        Returns:
            requests.Response: The response from the NFSe Nacional service.
        """
        token = company.get_focusnfe_token()
        url = f"{NFSE_URL[environment]}{API_ENDPOINT_NACIONAL['status']}{ref}"
        return self._make_focus_nfse_http_request("GET", url, token)

    @api.model
    def cancel_focus_nfse_nacional_document(
        self, ref, cancel_reason, company, environment
    ):
        """Cancel an electronic fiscal document for NFSe Nacional.

        Args:
            ref (str): The document reference.
            cancel_reason (str): The reason for cancellation.
            company (recordset): The company record.
            environment (str): The environment (1=production, 2=homologation).

        Returns:
            requests.Response: The response from the NFSe Nacional service.
        """
        token = company.get_focusnfe_token()
        data = {"justificativa": cancel_reason}
        url = f"{NFSE_URL[environment]}{API_ENDPOINT_NACIONAL['cancelamento']}{ref}"
        return self._make_focus_nfse_http_request(
            "DELETE", url, token, data=json.dumps(data)
        )
