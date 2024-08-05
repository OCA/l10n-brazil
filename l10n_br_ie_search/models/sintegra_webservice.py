# Copyright 2023 KMEE - Breno Oliveira Dias
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from erpbrasil.base.misc import punctuation_rm

from odoo import _, api, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SintegraWebservice(models.AbstractModel):
    _inherit = "l10n_br_cnpj_search.webservice.abstract"

    @api.model
    def _get_query(self, cnpj, token):
        return {
            "token": token,
            "cnpj": punctuation_rm(cnpj),
            "plugin": "ST",
        }

    @api.model
    def _get_token(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_br_ie_search.sintegra_token")
        )

    @api.model
    def sintegra_validate(self, response):
        self._validate(response)
        data = response.json()
        if data.get("status") == "ERROR":
            raise ValidationError(_(data.get("message")))
        return data

    @api.model
    def _validate(self, response):
        if response.status_code != 200:
            raise ValidationError(_("%s" % response.reason))

    @api.model
    def _sintegra_import_data(self, data):
        res = {
            "inscr_est": self.get_data(data, "inscricao_estadual"),
        }
        return res

    @api.model
    def get_data(self, data, name, title=False, lower=False):
        value = False
        if data.get(name):
            value = data[name]
            if lower:
                value = value.lower()
            elif title:
                value = value.title()

        return value
