# Copyright 2022 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from erpbrasil.base.misc import punctuation_rm
from requests import get

from odoo import _, models
from odoo.exceptions import UserError


class PartyMixinCRM(models.AbstractModel):
    _inherit = "l10n_br_base.party.mixin"

    def search_cnpj(self):
        """Search CNPJ by the chosen API"""
        if not self.cnpj_cpf:
            raise UserError(_("Por favor insira o CNPJ"))

        if self.cnpj_validation_disabled():
            raise UserError(
                _(
                    "It is necessary to activate the option to validate de CNPJ to use this "
                    + "functionality."
                )
            )

        cnpj_cpf = punctuation_rm(self.cnpj_cpf)
        webservice = self.env["l10n_br_cnpj_search.webservice.abstract"]
        response = get(
            webservice.get_api_url(cnpj_cpf), headers=webservice.get_headers()
        )

        data = webservice.validate(response)
        values = webservice.import_data(data)
        self.write(values)
