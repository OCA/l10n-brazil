# Copyright 2022 KMEE - Luis Felipe Mileo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from erpbrasil.base.misc import punctuation_rm

from odoo import api, models


class CNPJWebserviceFiscal(models.AbstractModel):
    """Each specific webservice can extend the model by adding
    its own methods, using the webservice name (same as selection in config)
    as a prefix for the new methods.

    Methods that should be added in a webservice-specific implementation:
        - <name>_get_api_url(self, cnpj)
        - <name>_get_api_headers(self)
        - <name>_validate(self, response)
        - <name>_import_data(self, data)
    """

    _inherit = "l10n_br_cnpj_search.webservice.abstract"
    _description = "CNPJ Webservice"

    @api.model
    def _get_cnae(self, raw_code):
        code = punctuation_rm(raw_code)
        cnae_id = False

        if code:
            formatted_code = code[0:4] + "-" + code[4] + "/" + code[5:]
            cnae_id = (
                self.env["l10n_br_fiscal.cnae"]
                .search([("code", "=", formatted_code)])
                .id
            )

        return cnae_id
