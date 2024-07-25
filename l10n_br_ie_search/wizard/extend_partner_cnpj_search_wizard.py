# Copyright 2023 KMEE - Breno Oliveira Dias
# Copyright (C) 2024-Today - Engenere (<https://engenere.one>).
# @author Cristiano Mafra Junior
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import requests
from erpbrasil.edoc.nfe import NFe as edoc_nfe
from erpbrasil.transmissao import TransmissaoSOAP
from requests import Session

from odoo import api, models

SINTEGRA_URL = "https://www.sintegraws.com.br/api/v1/execute-api.php"
SINTEGRA_TIMEOUT = 60


class ExtendPartnerCnpjSearchWizard(models.TransientModel):
    _inherit = "partner.search.wizard"

    def _get_partner_ie(self, state_code, cnpj):
        webservice = self.env["l10n_br_cnpj_search.webservice.abstract"]
        if self._provider() == "sefaz":
            processo = self._processador()
            response = webservice.sefaz_search(state_code, cnpj, processo)
            data = webservice.sefaz_validate(response)
            values = webservice._sefaz_import_data(data)
            return values
        elif self._provider() == "sintegraws":
            response = requests.get(
                SINTEGRA_URL,
                data="",
                params=webservice._get_query(cnpj, webservice._get_token()),
                timeout=SINTEGRA_TIMEOUT,
            )
            data = webservice.sintegra_validate(response)
            values = webservice._sintegra_import_data(data)
            return values

    @api.model
    def _provider(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_br_ie_search.ie_search")
        )

    @api.model
    def _get_partner_values(self, cnpj_cpf):
        values = super()._get_partner_values(cnpj_cpf)
        state_id = self.env["res.country.state"].browse(values["state_id"])
        ie_values = self._get_partner_ie(state_code=state_id.code, cnpj=cnpj_cpf)
        if ie_values:
            values.update(ie_values)
        return values

    @api.model
    def _processador(self):
        company = self.env.company
        certificado = company._get_br_ecertificate()
        session = Session()
        session.verify = False
        transmissao = TransmissaoSOAP(certificado, session)
        return edoc_nfe(
            transmissao,
            company.state_id.ibge_code,
            versao=company.nfe_version,
            ambiente=company.nfe_environment,
        )
