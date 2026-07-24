# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""NFSe Municipal integration with FocusNFE."""

import json

from odoo import api

from .base import FocusnfeNfseBase
from .constants import API_ENDPOINT, NFSE_URL


class FocusnfeNfse(FocusnfeNfseBase):
    """FocusNFE NFSe Municipal implementation."""

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
        return super()._make_focus_nfse_http_request(
            method, url, token, data, params, service_name="NFSe"
        )

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
            environment (str): The environment (1=production, 2=homologation).

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

        vals = {
            "prestador": self._prepare_provider_data(rps_info, company),
            "servico": self._prepare_service_data(service_info, company),
            "tomador": self._prepare_recipient_data(
                recipient_info, recipient_identification, company
            ),
            "razao_social": company.name,
            "data_emissao": rps_info.get("data_emissao"),
            "incentivador_cultural": rps_info.get("incentivador_cultural", False),
            "natureza_operacao": rps_info.get("natureza_operacao"),
            "optante_simples_nacional": rps_info.get("optante_simples_nacional", False),
            "regime_especial_tributacao": rps_info.get("natureza_operacao"),
            "finalidade_emissao": rps_info.get("finalidade_emissao", "0"),
            "consumidor_final": rps_info.get("consumidor_final", False),
            "indicador_destinatario": rps_info.get("indicador_destinatario", "9"),
            "operacao_onerosa": rps_info.get("operacao_onerosa", False),
            "status": rps_info.get("status"),
            "informacoes_adicionais_contribuinte": (
                rps_info.get("customer_additional_data", False)[:256]
                if rps_info.get("customer_additional_data")
                else False
            ),
        }
        codigo_obra = rps_info.get("codigo_obra", False)
        art = rps_info.get("art", False)

        if codigo_obra:
            vals["codigo_obra"] = codigo_obra

        if art:
            vals["art"] = art

        return vals

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
        situacao_tributaria_pis_cofins = (
            service.get("situacao_tributaria_pis")
            or service.get("situacao_tributaria_cofins")
            or ""
        )
        if situacao_tributaria_pis_cofins == "99":
            situacao_tributaria_pis_cofins = "00"

        base_calculo_pis = service.get("base_calculo_pis", 0)
        base_calculo_cofins = service.get("base_calculo_cofins", 0)
        base_calculo_pis_cofins = round(
            base_calculo_pis if base_calculo_pis else base_calculo_cofins, 2
        )
        if situacao_tributaria_pis_cofins:
            if situacao_tributaria_pis_cofins in ["00", "08", "09"]:
                base_calculo_pis_cofins = 0.0
            elif not base_calculo_pis_cofins:
                base_calculo_pis_cofins = round(service.get("valor_servicos", 0), 2)

        pis_retido = bool(service.get("valor_pis_retido"))
        cofins_retido = bool(service.get("valor_cofins_retido"))
        csll_retido = bool(service.get("valor_csll_retido"))
        inss_retido = bool(service.get("valor_inss_retido"))
        ir_retido = bool(service.get("valor_ir_retido"))
        icms_retido = bool(service.get("valor_icms_retido"))

        valor_servicos = round(service.get("valor_servicos", 0), 2)
        base_calculo_csll = valor_servicos if csll_retido else 0.0
        base_calculo_inss = valor_servicos if inss_retido else 0.0
        base_calculo_ir = valor_servicos if ir_retido else 0.0
        base_calculo_icms = valor_servicos if icms_retido else 0.0

        tipo_retencao_pis_cofins = {
            (False, False, False): "0",
            (True, True, True): "3",
            (True, True, False): "4",
            (True, False, False): "5",
            (False, True, False): "6",
            (False, True, True): "7",
            (False, False, True): "8",
            (True, False, True): "9",
        }[(pis_retido, cofins_retido, csll_retido)]

        return {
            "aliquota": service.get("aliquota")
            if company.focusnfe_tax_rate_format == "decimal"
            else round(service.get("aliquota", 0.0) * 100, 1),
            **(
                {"base_calculo": round(service.get("base_calculo", 0), 2)}
                if service.get("base_calculo", 0)
                else {}
            ),
            "discriminacao": service.get("discriminacao"),
            "iss_retido": service.get("iss_retido"),
            **(
                {
                    "situacao_tributaria_pis_cofins": situacao_tributaria_pis_cofins,
                    "base_calculo_pis_cofins": base_calculo_pis_cofins,
                    "aliquota_pis": round(service.get("aliquota_pis", 0), 2),
                    "aliquota_cofins": round(service.get("aliquota_cofins", 0), 2),
                }
                if situacao_tributaria_pis_cofins
                else {}
            ),
            **(
                {"tipo_retencao_pis_cofins": tipo_retencao_pis_cofins}
                if pis_retido or cofins_retido or csll_retido
                else {}
            ),
            "aliquota_csll": round(service.get("aliquota_csll", 0), 2),
            "aliquota_ir": round(service.get("aliquota_ir", 0), 2),
            "aliquota_inss": round(service.get("aliquota_inss", 0), 2),
            "aliquota_cp": round(service.get("aliquota_inss", 0), 2),
            "aliquota_icms": round(service.get("aliquota_icms", 0), 2),
            "base_calculo_csll": base_calculo_csll,
            "base_calculo_ir": base_calculo_ir,
            "base_calculo_inss": base_calculo_inss,
            "base_calculo_cp": base_calculo_inss,
            "base_calculo_icms": base_calculo_icms,
            "inss_retido": inss_retido,
            "ir_retido": ir_retido,
            "icms_retido": icms_retido,
            **(
                {"codigo_municipio": service.get("municipio_prestacao_servico")}
                if service.get("municipio_prestacao_servico") != "3507605"
                else {}
            ),
            "codigo_municipio_incidencia": service.get("municipio_prestacao_servico"),
            "item_lista_servico": service.get(company.focusnfe_nfse_service_type_value),
            "codigo_cnae": service.get(company.focusnfe_nfse_cnae_code_value),
            "valor_iss": round(service.get("valor_iss", 0), 2),
            "valor_iss_retido": round(service.get("valor_iss_retido", 0), 2),
            "valor_pis": round(service.get("valor_pis_retido", 0), 2),
            "valor_cofins": round(service.get("valor_cofins_retido", 0), 2),
            "valor_inss": round(service.get("valor_inss_retido", 0), 2),
            "valor_ir": round(service.get("valor_ir_retido", 0), 2),
            "valor_csll": round(service.get("valor_csll_retido", 0), 2),
            "valor_deducoes": round(service.get("valor_deducoes", 0), 2),
            "fonte_total_tributos": service.get("fonte_total_tributos", "IBPT"),
            "desconto_incondicionado": round(
                service.get("valor_desconto_incondicionado", 0), 2
            ),
            "desconto_condicionado": round(service.get("desconto_condicionado", 0), 2),
            "outras_retencoes": round(service.get("outras_retencoes", 0), 2),
            "valor_servicos": round(service.get("valor_servicos", 0), 2),
            "valor_liquido": round(service.get("valor_liquido_nfse", 0), 2),
            "codigo_tributario_municipio": service.get("codigo_tributacao_municipio"),
            "codigo_nbs": service.get("codigo_nbs"),
            "codigo_indicador_operacao": service.get("codigo_indicador_operacao"),
            "ibs_cbs_classificacao_tributaria": service.get(
                "ibs_cbs_classificacao_tributaria"
            ),
            "ibs_cbs_situacao_tributaria": service.get("ibs_cbs_situacao_tributaria"),
            "codigo_tributacao_nacional_iss": service.get("codigo_tributacao_nacional"),
            "ibs_cbs_base_calculo": service.get("ibs_cbs_base_calculo"),
            "ibs_uf_aliquota": round(service.get("ibs_uf_aliquota", 0), 2)
            if service.get("ibs_uf_aliquota")
            else None,
            "ibs_mun_aliquota": 0.0,
            "cbs_aliquota": round(service.get("cbs_aliquota", 0), 2)
            if service.get("cbs_aliquota")
            else None,
            "ibs_uf_valor": round(service.get("ibs_uf_valor", 0), 2)
            if service.get("ibs_uf_valor")
            else None,
            "ibs_mun_valor": 0.0,
            "cbs_valor": round(service.get("cbs_valor", 0), 2)
            if service.get("cbs_valor")
            else None,
            "ibs_uf_percentual_diferimento": 0.0,
            "ibs_mun_percentual_diferimento": 0.0,
            "cbs_percentual_diferimento": 0.0,
        }

    def _prepare_recipient_data(self, recipient, identification, company):
        """Construct the recipient section of the payload.

        Args:
            recipient (dict): Information about the service recipient.
            identification (dict): The recipient's identification (CPF or CNPJ).
            company (recordset): The company record.

        Returns:
            dict: The recipient section of the payload.
        """
        if recipient.get("nif"):
            recipient["codigo_municipio"] = company.city_id.ibge_code

        return {
            **identification,
            "nif": recipient.get("nif"),
            "nif_motivo_ausencia": recipient.get("nif_motivo_ausencia"),
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
            environment (str): The environment (1=production, 2=homologation).

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
            environment (str): The environment (1=production, 2=homologation).

        Returns:
            requests.Response: The response from the NFSe service.
        """
        token = company.get_focusnfe_token()
        data = {"justificativa": cancel_reason}
        url = f"{NFSE_URL[environment]}{API_ENDPOINT['cancelamento']}{ref}"
        return self._make_focus_nfse_http_request(
            "DELETE", url, token, data=json.dumps(data)
        )
