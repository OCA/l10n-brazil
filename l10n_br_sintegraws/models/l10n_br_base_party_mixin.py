# Copyright 2023 KMEE - Breno Oliveira Dias
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from requests import get

from odoo import _, api, models
from odoo.exceptions import UserError


class PartyMixin(models.AbstractModel):
    _inherit = "l10n_br_base.party.mixin"

    def search_cnpj(self):
        """Search state subscription"""

        super().search_cnpj()
        self.ie_search()

    @api.model
    def ie_search(self):
        if self.enabled_ie_search():
            webservice = self.env["l10n_br_cnpj_search.webservice.abstract"]
            response = get(
                webservice.sintegra_get_api_url(),
                data="",
                params=webservice._get_query(self.cnpj_cpf, webservice._get_token()),
            )
            data = webservice.sintegra_validate(response)
            values = webservice._sintegra_import_data(data)
            self.write(values)
        else:
            raise UserError(
                _(
                    "It is necessary to activate the option to use the IE search to use this "
                    + "functionality."
                )
            )

    @api.model
    def enabled_ie_search(self):
        ie_search_enabled = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_br_sintegraws.ie_search")
        )
        return ie_search_enabled
