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


def filter_focusnfe_nacional(record):
    return (
        record.company_id.provedor_nfse == "focusnfe"
        and record.company_id.focusnfe_nfse_type == "nfse_nacional"
    )


def filter_focusnfe_municipal(record):
    return (
        record.company_id.provedor_nfse == "focusnfe"
        and record.company_id.focusnfe_nfse_type == "nfse"
    )


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
            if response.status_code == 422:
                payload = response.json()
                msg = payload.get("mensagem") or ""
                raise UserError(f"Error communicating with NFSe service: {msg}")
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
        return {
            "aliquota": service.get("aliquota")
            if company.focusnfe_tax_rate_format == "decimal"
            else round(service.get("aliquota", 0.0) * 100, 1),
            "base_calculo": round(service.get("base_calculo", 0), 2),
            "discriminacao": service.get("discriminacao"),
            "iss_retido": service.get("iss_retido"),
            "codigo_municipio": service.get("municipio_prestacao_servico"),
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
            "codigo_classificacao_tributaria": service.get(
                "codigo_classificacao_tributaria"
            ),
            "codigo_situacao_tributaria": service.get("codigo_situacao_tributaria"),
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


API_ENDPOINT_NACIONAL = {
    "envio": "/v2/nfsen",
    "status": "/v2/nfsen/",
    "resposta": "/v2/nfsen/",
    "cancelamento": "/v2/nfsen/",
}


class FocusnfeNfseNacional(models.AbstractModel):
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
        auth = (token, "")
        try:
            response = requests.request(  # pylint: disable=external-request-timeout
                method,
                url,
                data=data,
                params=params,
                auth=auth,
            )
            if response.status_code == 422:
                payload = response.json()
                msg = payload.get("mensagem") or ""
                raise UserError(
                    f"Error communicating with NFSe Nacional service: {msg}"
                )
            response.raise_for_status()  # Raises an error for 4xx/5xx responses
            return response
        except requests.HTTPError as e:
            raise UserError(
                _("Error communicating with NFSe Nacional service: %s") % e
            ) from e

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

        # Prepare emission date with timezone
        emission_date = rps_info.get("data_emissao", "")
        if emission_date and not emission_date.endswith(("-0300", "-0200", "+0000")):
            # Add timezone if not present (assuming -0300 for Brazil)
            emission_date = emission_date + "-0300"

        # Prepare competence date (YYYY-MM-DD)
        competence_date = (
            rps_info.get("data_emissao", "")[:10]
            if rps_info.get("data_emissao")
            else ""
        )

        # Get municipality code
        codigo_municipio_emissora = company.city_id.ibge_code or ""

        # Prepare provider data
        cnpj_prestador = rps_info.get("cnpj", "")
        cpf_prestador = rps_info.get("cpf", "")
        # Determinar se é CPF ou CNPJ baseado no tamanho
        # CPF tem 11 dígitos, CNPJ tem 14 dígitos
        # Limpar formatação para verificar o tamanho
        cpf_prestador_limpo = (
            cpf_prestador.replace(".", "").replace("-", "") if cpf_prestador else ""
        )
        cnpj_prestador_limpo = (
            cnpj_prestador.replace(".", "").replace("/", "").replace("-", "")
            if cnpj_prestador
            else ""
        )
        is_cpf_prestador = bool(cpf_prestador_limpo and len(cpf_prestador_limpo) == 11)
        is_cnpj_prestador = bool(
            cnpj_prestador_limpo and len(cnpj_prestador_limpo) == 14
        )

        # TODO: aparentemente nao é enviado
        # inscricao_municipal_prestador = rps_info.get("inscricao_municipal", "")

        # Get simple national option code
        # TODO: melhorar a lógica para obter o código da opção simples nacional
        # codigo_opcao_simples_nacional
        # Tag XML opSimpNac
        # obrigatório
        # Situação perante Simples Nacional:
        # 1: Não Optante;
        # 2: Optante - Microempreendedor Individual (MEI);
        # 3: Optante - Microempresa ou Empresa de Pequeno Porte (ME/EPP).
        optante_simples = rps_info.get("optante_simples_nacional", "1")
        codigo_opcao_simples_nacional = "2" if optante_simples == "1" else "1"

        # Get special taxation regime
        # TODO: melhorar a lógica para obter o código do regime especial de tributação
        # regime_especial_tributacao
        # Tag XML regEspTrib
        # obrigatório
        # Tipos de Regimes Especiais de Tributação Municipal:
        # 0: Nenhum;
        # 1: Ato Cooperado (Cooperativa);
        # 2: Estimativa;
        # 3: Microempresa Municipal;
        # 4: Notário ou Registrador;
        # 5: Profissional Autônomo;
        # 6: Sociedade de Profissionais.
        regime_especial_tributacao = (
            rps_info.get("regime_especial_tributacao", "0") or "0"
        )

        # Prepare recipient data
        cnpj_tomador = recipient_info.get("cnpj", "")
        cpf_tomador = recipient_info.get("cpf", "")
        # Determinar se é CPF ou CNPJ baseado no tamanho
        # CPF tem 11 dígitos, CNPJ tem 14 dígitos
        # Limpar formatação para verificar o tamanho
        cpf_limpo = cpf_tomador.replace(".", "").replace("-", "") if cpf_tomador else ""
        cnpj_limpo = (
            cnpj_tomador.replace(".", "").replace("/", "").replace("-", "")
            if cnpj_tomador
            else ""
        )
        is_cpf = bool(cpf_limpo and len(cpf_limpo) == 11)
        is_cnpj = bool(cnpj_limpo and len(cnpj_limpo) == 14)
        razao_social_tomador = recipient_info.get("razao_social", "")
        codigo_municipio_tomador = recipient_info.get("codigo_municipio", "")
        # CEP can be int or string, convert to string
        cep_tomador = recipient_info.get("cep", "")
        if isinstance(cep_tomador, int):
            cep_tomador = str(cep_tomador)
        logradouro_tomador = recipient_info.get("endereco", "")
        numero_tomador = recipient_info.get("numero", "")
        complemento_tomador = recipient_info.get("complemento", "")
        bairro_tomador = recipient_info.get("bairro", "")
        # Telefone is not in recipient_info, leave empty
        telefone_tomador = recipient_info.get("telefone", "")
        email_tomador = recipient_info.get("email", "")

        # Prepare service data
        codigo_municipio_prestacao = service_info.get("municipio_prestacao_servico", "")
        # For NFSe Nacional, we need codigo_tributacao_nacional_iss
        # This should come from the service type or city taxation code
        codigo_tributacao_nacional_iss = service_info.get(
            "codigo_tributacao_nacional_iss", ""
        )
        if not codigo_tributacao_nacional_iss:
            # Try to get from city taxation code
            codigo_tributacao_nacional_iss = service_info.get(
                "codigo_tributacao_municipio", ""
            )
        if not codigo_tributacao_nacional_iss:
            # Fallback to item_lista_servico (service type code)
            codigo_tributacao_nacional_iss = service_info.get("item_lista_servico", "")

        descricao_servico = service_info.get("discriminacao", "")
        valor_servico = round(service_info.get("valor_servicos", 0), 2)

        # TODO: melhorar a lógica para obter o código da tributação ISS
        # tributacao_iss
        # Tag XML tribISSQN
        # obrigatório
        # Tributação do ISSQN sobre o serviço prestado:
        # 1: Operação tributável;
        # 2: Imunidade;
        # 3: Exportação de serviço;
        # 4: Não Incidência.
        tributacao_iss = 1

        # TODO: melhorar a lógica para obter o código da retencao ISS
        # tipo_retencao_iss
        # Tag XML tpRetISSQN
        # Tipo de retencao do ISSQN:
        # 1: Não Retido;
        # 2: Retido pelo Tomador;
        # 3: Retido pelo Intermediario.
        tipo_retencao_iss = "2" if service_info.get("iss_retido") == "1" else "1"

        # TODO: tratar percentual_aliquota_relativa_municipio - aparentemente
        # nao é enviado
        # # Campos adicionais para NFSe Nacional
        # # percentual_aliquota_relativa_municipio - usar a alíquota do serviço
        # aliquota_servico = service_info.get("aliquota", 0)
        # # A alíquota vem em decimal (0-1), converter para percentual (0-100)
        # percentual_aliquota_relativa_municipio = (
        #     round(aliquota_servico * 100, 2) if aliquota_servico else 0.0
        # )

        # Situação tributária PIS/COFINS - usar PIS se disponível, senão COFINS
        situacao_tributaria_pis_cofins = (
            service_info.get("situacao_tributaria_pis", "")
            or service_info.get("situacao_tributaria_cofins", "")
            or ""
        )
        # Ajuste: Se a situação tributária for 99, alterar para 00
        if situacao_tributaria_pis_cofins == "99":
            situacao_tributaria_pis_cofins = "00"

        # Base de cálculo PIS/COFINS - usar de qualquer um que tenha valor
        base_calculo_pis = service_info.get("base_calculo_pis", 0)
        base_calculo_cofins = service_info.get("base_calculo_cofins", 0)
        base_calculo_pis_cofins = round(
            base_calculo_pis if base_calculo_pis else base_calculo_cofins, 2
        )
        # Validação: Se o CST for 0, 8 ou 9, a base de cálculo deve ser 0
        # Se o CST for diferente de 0, 8 ou 9, a base de cálculo deve ser informada
        if situacao_tributaria_pis_cofins:
            if situacao_tributaria_pis_cofins in ["00", "08", "09"]:
                # CST 0, 8 ou 9: base de cálculo deve ser 0
                base_calculo_pis_cofins = 0.0
            else:
                # CST diferente de 0, 8 ou 9: base de cálculo deve ser informada
                # Se não houver base de cálculo, usar o valor do serviço
                if not base_calculo_pis_cofins or base_calculo_pis_cofins == 0:
                    base_calculo_pis_cofins = round(valor_servico, 2)
        # Alíquotas PIS e COFINS devem ter sempre 2 casas decimais
        # (padrão da API: 0|0\.[0-9]{2}|[1-9]{1}[0-9]{0,1}(\.[0-9]{2})?)
        # Formatamos como string para garantir 2 casas decimais na serialização JSON
        aliquota_pis_raw = round(service_info.get("aliquota_pis", 0), 2)
        aliquota_pis = f"{aliquota_pis_raw:.2f}"
        aliquota_cofins_raw = round(service_info.get("aliquota_cofins", 0), 2)
        aliquota_cofins = f"{aliquota_cofins_raw:.2f}"
        valor_pis = round(service_info.get("valor_pis", 0), 2)
        valor_cofins = round(service_info.get("valor_cofins", 0), 2)
        tipo_retencao_pis_cofins = service_info.get("tipo_retencao_pis_cofins", "2")
        # Valor CP (Contribuição Previdenciária) - geralmente é o INSS
        valor_cp = round(service_info.get("valor_inss_retido", 0), 2)
        # Valor IRRF
        valor_irrf = round(service_info.get("valor_ir_retido", 0), 2)
        # Valor CSLL
        valor_csll = round(service_info.get("valor_csll_retido", 0), 2)

        # TODO: Aparentemente nao sao enviados
        # # Campos de total de tributos (opcionais - podem vir do IBPT
        # # ou ser calculados)
        # # Por enquanto, deixamos vazios ou calculamos se disponível
        # valor_total_tributos_federais = round(
        #     valor_pis + valor_cofins + valor_irrf + valor_csll + valor_cp, 2
        # )
        # valor_total_tributos_estaduais = (
        #     0.0
        # )  # Para NFSe geralmente não há tributos estaduais
        # valor_total_tributos_municipais =
        #   round(service_info.get("valor_iss", 0), 2)
        # # Percentuais (calculados se base disponível)
        # percentual_total_tributos_federais = (
        #     round((valor_total_tributos_federais / valor_servico * 100), 2)
        #     if valor_servico > 0
        #     else 0.0
        # )
        # percentual_total_tributos_estaduais = 0.0
        # percentual_total_tributos_municipais = (
        #     round((valor_total_tributos_municipais / valor_servico * 100), 2)
        #     if valor_servico > 0
        #     else 0.0
        # )
        # # Indicador de total de tributação (0 = Não informar valores estimados)
        # indicador_total_tributacao = "0"
        # # Percentual total tributos Simples Nacional (opcional)
        # percentual_total_tributos_simples_nacional = 0.0

        payload = {
            "data_emissao": emission_date,
            "data_competencia": competence_date,
            "codigo_municipio_emissora": str(codigo_municipio_emissora)
            if codigo_municipio_emissora
            else "",
            # Enviar CNPJ ou CPF conforme o tipo do prestador
            # Enviar sem formatação (apenas números)
            # Só incluir o campo no payload se for do tipo correto
            **({"cnpj_prestador": cnpj_prestador_limpo} if is_cnpj_prestador else {}),
            **({"cpf_prestador": cpf_prestador_limpo} if is_cpf_prestador else {}),
            # TODO: aparentemente nao é enviado
            # "inscricao_municipal_prestador": inscricao_municipal_prestador or "",
            "codigo_opcao_simples_nacional": codigo_opcao_simples_nacional,
            "regime_especial_tributacao": regime_especial_tributacao,
            # Enviar CNPJ ou CPF conforme o tipo do tomador
            # Enviar sem formatação (apenas números)
            # Só incluir o campo no payload se for do tipo correto
            **({"cnpj_tomador": cnpj_limpo} if is_cnpj else {}),
            **({"cpf_tomador": cpf_limpo} if is_cpf else {}),
            "razao_social_tomador": razao_social_tomador,
            "codigo_municipio_tomador": str(codigo_municipio_tomador)
            if codigo_municipio_tomador
            else "",
            "cep_tomador": cep_tomador or "",
            "logradouro_tomador": logradouro_tomador,
            "numero_tomador": numero_tomador or "",
            "complemento_tomador": complemento_tomador or "",
            "bairro_tomador": bairro_tomador,
            "telefone_tomador": telefone_tomador or "",
            "email_tomador": email_tomador or "",
            "codigo_municipio_prestacao": str(codigo_municipio_prestacao)
            if codigo_municipio_prestacao
            else "",
            "codigo_tributacao_nacional_iss": codigo_tributacao_nacional_iss,
            "descricao_servico": descricao_servico,
            "valor_servico": valor_servico,
            "tributacao_iss": str(tributacao_iss),
            "tipo_retencao_iss": str(tipo_retencao_iss),
            # TODO: tratar percentual_aliquota_relativa_municipio
            # percentual_aliquota_relativa_municipio deve ser em percentual (0-100)
            # percentual_aliquota_relativa_municipio
            # Decimal[1.2]Tag XML pAliq
            # Valor da alíquota (%) do serviço
            # prestado relativo ao município sujeito
            # ativo (município de incidência) do ISSQN. Se
            # o município de incidência pertence ao Sistema
            # Nacional NFS-e a alíquota estará parametrizada e, portanto,
            # será fornecida pelo sistema. Se o município de incidência
            # não pertence ao Sistema Nacional NFS-e a alíquota não estará
            # parametrizada e, por isso, deverá ser fornecida pelo emitente.
            # "percentual_aliquota_relativa_municipio": (
            #     percentual_aliquota_relativa_municipio
            # ),
            "situacao_tributaria_pis_cofins": situacao_tributaria_pis_cofins or "",
            "base_calculo_pis_cofins": round(base_calculo_pis_cofins, 2),
            "aliquota_pis": aliquota_pis,
            "aliquota_cofins": aliquota_cofins,
            "valor_pis": valor_pis,
            "valor_cofins": valor_cofins,
            "tipo_retencao_pis_cofins": tipo_retencao_pis_cofins,
            "valor_cp": valor_cp,
            "valor_irrf": valor_irrf,
            "valor_csll": valor_csll,
            # TODO: aparentemente nao é enviado
            # "valor_total_tributos_federais": valor_total_tributos_federais,
            # "valor_total_tributos_estaduais": valor_total_tributos_estaduais,
            # "valor_total_tributos_municipais":
            #   valor_total_tributos_municipais,
            # "percentual_total_tributos_federais":
            #   percentual_total_tributos_federais,
            # "percentual_total_tributos_estaduais":
            #   percentual_total_tributos_estaduais,
            # "percentual_total_tributos_municipais": (
            #     percentual_total_tributos_municipais
            # ),
            # "indicador_total_tributacao": indicador_total_tributacao,
            # "percentual_total_tributos_simples_nacional": (
            #     percentual_total_tributos_simples_nacional
            # ),
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

    def _process_authorized_status_nacional(self, record, json_data):
        """Process authorized status for NFSe Nacional."""
        aware_datetime = datetime.strptime(
            json_data["data_emissao"], "%Y-%m-%dT%H:%M:%S%z"
        )
        utc_datetime = aware_datetime.astimezone(pytz.utc)
        naive_datetime = utc_datetime.replace(tzinfo=None)
        record.write(
            {
                "verify_code": json_data.get("codigo_verificacao", ""),
                "document_number": json_data.get("numero", ""),
                "authorization_date": naive_datetime,
            }
        )

        xml_path = json_data.get("caminho_xml_nota_fiscal", "")
        if xml_path:
            xml = requests.get(
                NFSE_URL[record.nfse_environment] + xml_path,
                timeout=TIMEOUT,
            ).content.decode("utf-8")

            if not record.authorization_event_id:
                record._document_export()

            if record.authorization_event_id:
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
                    url_danfse = json_data.get("url_danfse", "")
                    if url_danfse:
                        pdf_content = requests.get(
                            url_danfse,
                            timeout=TIMEOUT,
                            verify=record.company_id.nfse_ssl_verify,
                        ).content
                        if pdf_content.startswith(
                            b"%PDF-"
                        ) and pdf_content.strip().endswith(b"%%EOF"):
                            record.make_focus_nfse_pdf(pdf_content)

    def _process_authorized_status_municipal(self, record, json_data):
        """Process authorized status for NFSe Municipal."""
        aware_datetime = datetime.strptime(
            json_data["data_emissao"], "%Y-%m-%dT%H:%M:%S%z"
        )
        utc_datetime = aware_datetime.astimezone(pytz.utc)
        naive_datetime = utc_datetime.replace(tzinfo=None)
        record.write(
            {
                "verify_code": json_data["codigo_verificacao"],
                "document_number": json_data["numero"],
                "authorization_date": naive_datetime,
            }
        )

        xml = requests.get(
            NFSE_URL[record.nfse_environment] + json_data["caminho_xml_nota_fiscal"],
            timeout=TIMEOUT,
        ).content.decode("utf-8")

        if not record.authorization_event_id:
            record._document_export()

        if record.authorization_event_id:
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
                pdf_content = requests.get(
                    json_data["url"],
                    timeout=TIMEOUT,
                    verify=record.company_id.nfse_ssl_verify,
                ).content
                if not pdf_content.startswith(
                    b"%PDF-"
                ) and not pdf_content.strip().endswith(b"%%EOF"):
                    pdf_content = requests.get(
                        json_data["url_danfse"],
                        timeout=TIMEOUT,
                        verify=record.company_id.nfse_ssl_verify,
                    ).content
                if pdf_content.startswith(b"%PDF-") and pdf_content.strip().endswith(
                    b"%%EOF"
                ):
                    record.make_focus_nfse_pdf(pdf_content)

    def _process_error_status(self, record, json_data):
        """Process error authorization status."""
        erros = json_data.get("erros", [])
        error_msg = erros[0]["mensagem"] if erros else "Erro na autorização"
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
                    json["status"] == "autorizado"
                    and record.state_edoc != SITUACAO_EDOC_AUTORIZADA
                ):
                    self._process_authorized_status_nacional(record, json)
                elif json["status"] == "erro_autorizacao":
                    self._process_error_status(record, json)
                elif json["status"] == "cancelado":
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
                    json["status"] == "autorizado"
                    and record.state_edoc != SITUACAO_EDOC_AUTORIZADA
                ):
                    self._process_authorized_status_municipal(record, json)
                elif json["status"] == "erro_autorizacao":
                    record.write(
                        {
                            "edoc_error_message": json["erros"][0]["mensagem"],
                        }
                    )
                    record._change_state(SITUACAO_EDOC_REJEITADA)
                elif json["status"] == "cancelado":
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
        if not pdf_content.startswith(b"%PDF-") and not pdf_content.strip().endswith(
            b"%%EOF"
        ):
            pdf_content = requests.get(
                status_json["url_danfse"],
                timeout=TIMEOUT,
                verify=record.company_id.nfse_ssl_verify,
            ).content
        if pdf_content.startswith(b"%PDF-") and pdf_content.strip().endswith(b"%%EOF"):
            record.make_focus_nfse_pdf(pdf_content)

    def _process_cancel_nacional(self, record):
        """Process cancellation for NFSe Nacional."""
        ref = str(record.rps_number)

        status_response = record.env[
            "focusnfe.nfse.nacional"
        ].query_focus_nfse_nacional_by_ref(
            ref, record.company_id, record.nfse_environment
        )
        status_json = status_response.json()

        if status_response.status_code == 200:
            if (
                status_json.get("status") == "cancelado"
                and record.state_edoc != SITUACAO_EDOC_CANCELADA
            ):
                record.cancel_event_id = record.create_cancel_event(status_json, record)
                if record.company_id.focusnfe_nfse_force_odoo_danfse:
                    record.make_pdf()
                else:
                    url_danfse = status_json.get("url_danfse", "")
                    if url_danfse:
                        pdf_content = requests.get(
                            url_danfse,
                            timeout=TIMEOUT,
                            verify=record.company_id.nfse_ssl_verify,
                        ).content
                        if pdf_content.startswith(
                            b"%PDF-"
                        ) and pdf_content.strip().endswith(b"%%EOF"):
                            record.make_focus_nfse_pdf(pdf_content)
                return status_response

        response = record.env[
            "focusnfe.nfse.nacional"
        ].cancel_focus_nfse_nacional_document(
            ref, record.cancel_reason, record.company_id, record.nfse_environment
        )

        json = response.json()

        if response.status_code in [200, 400]:
            code = json.get("codigo", "")
            status = json.get("status", "")

            if code == "nfe_cancelada" or status == "cancelado":
                status_rps = record.env[
                    "focusnfe.nfse.nacional"
                ].query_focus_nfse_nacional_by_ref(
                    ref, record.company_id, record.nfse_environment
                )
                status_json = status_rps.json()

                record.cancel_event_id = record.create_cancel_event(status_json, record)
                if record.company_id.focusnfe_nfse_force_odoo_danfse:
                    record.make_pdf()
                else:
                    url_danfse = status_json.get("url_danfse", "")
                    if url_danfse:
                        pdf_content = requests.get(
                            url_danfse,
                            timeout=TIMEOUT,
                            verify=record.company_id.nfse_ssl_verify,
                        ).content
                        if pdf_content.startswith(
                            b"%PDF-"
                        ) and pdf_content.strip().endswith(b"%%EOF"):
                            record.make_focus_nfse_pdf(pdf_content)

                return response

            raise UserError(
                _(
                    "%(code)s - %(status)s",
                    code=response.status_code,
                    status=status,
                )
            )

        raise UserError(
            _(
                "%(code)s - %(msg)s",
                code=response.status_code,
                msg=json.get("mensagem", ""),
            )
        )

    def _process_cancel_municipal(self, record):
        """Process cancellation for NFSe Municipal."""
        ref = "rps" + record.rps_number

        status_response = record.env["focusnfe.nfse"].query_focus_nfse_by_rps(
            ref, 0, record.company_id, record.nfse_environment
        )
        status_json = status_response.json()

        if status_response.status_code == 200:
            if (
                status_json["status"] == "cancelado"
                and record.state_edoc != SITUACAO_EDOC_CANCELADA
            ):
                record.cancel_event_id = record.create_cancel_event(status_json, record)
                if record.company_id.focusnfe_nfse_force_odoo_danfse:
                    record.make_pdf()
                else:
                    record.fetch_and_verify_pdf_content(status_json, record)
                return status_response

        response = record.env["focusnfe.nfse"].cancel_focus_nfse_document(
            ref, record.cancel_reason, record.company_id, record.nfse_environment
        )

        json = response.json()

        if response.status_code in [200, 400]:
            code = json.get("codigo", "")
            status = json.get("status", "")

            # hack barueri - provisório
            if not code and record.company_id.city_id.ibge_code == "3505708":
                code = json.get("erros", [{}])[0].get("codigo", "")
                if code == "OK200":
                    code = "nfe_cancelada"

            if code == "nfe_cancelada" or status == "cancelado":
                status_rps = record.env["focusnfe.nfse"].query_focus_nfse_by_rps(
                    ref, 0, record.company_id, record.nfse_environment
                )
                status_json = status_rps.json()

                record.cancel_event_id = record.create_cancel_event(status_json, record)
                if record.company_id.focusnfe_nfse_force_odoo_danfse:
                    record.make_pdf()
                else:
                    record.fetch_and_verify_pdf_content(status_json, record)

                return response

            raise UserError(
                _(
                    "%(code)s - %(status)s",
                    code=response.status_code,
                    status=status,
                )
            )

        raise UserError(
            _(
                "%(code)s - %(msg)s",
                code=response.status_code,
                msg=json.get("mensagem", ""),
            )
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
                if json["status"] == "processando_autorizacao":
                    if record.state == "rejeitada":
                        record.state_edoc = SITUACAO_EDOC_ENVIADA
                    else:
                        record._change_state(SITUACAO_EDOC_ENVIADA)
            elif response.status_code == 422:
                code = json.get("codigo", "")
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

    def _process_send_municipal(self, record):
        """Process document send for NFSe Municipal."""
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
                code = json.get("codigo", "")
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
        # Iterar sobre cada registro individualmente, pois _document_status()
        # pode esperar um singleton em alguns casos
        for record in records:
            record._document_status()
