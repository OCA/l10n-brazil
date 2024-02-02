# Copyright 2023 KMEE - Breno Oliveira Dias
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from erpbrasil.edoc.nfe import NFe as edoc_nfe
from erpbrasil.transmissao import TransmissaoSOAP
from requests import Session, get

from odoo import api, models

SINTEGRA_URL = "https://www.sintegraws.com.br/api/v1/execute-api.php"


class PartyMixin(models.AbstractModel):
    _inherit = "l10n_br_base.party.mixin"

    def search_cnpj(self):
        """Search state subscription"""

        super().search_cnpj()
        self.ie_search()

    @api.model
    def ie_search(self, mockresponse=False):
        webservice = self.env["l10n_br_cnpj_search.webservice.abstract"]
        if self._provider() == "sefaz":
            processo = self._processador()
            response = (
                webservice.sefaz_search(self.state_id.code, self.cnpj_cpf, processo)
                if not mockresponse
                else mockresponse
            )
            data = webservice.sefaz_validate(response)
            values = webservice._sefaz_import_data(data)
            self.write(values)
        elif self._provider() == "sintegraws":
            response = (
                get(
                    SINTEGRA_URL,
                    data="",
                    params=webservice._get_query(
                        self.cnpj_cpf, webservice._get_token()
                    ),
                )
                if not mockresponse
                else mockresponse
            )

            data = webservice.sintegra_validate(response)
            values = webservice._sintegra_import_data(data)
            self.write(values)

    @api.model
    def _provider(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_br_ie_search.ie_search")
        )

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
