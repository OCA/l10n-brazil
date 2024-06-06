# Copyright 2022 KMEE - Luis Felipe Mileo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from erpbrasil.base.misc import punctuation_rm

from odoo import _, api, models
from odoo.exceptions import ValidationError


class CNPJWebservice(models.AbstractModel):
    """Each specific webservice can extend the model by adding
    its own methods, using the webservice name (same as selection in config)
    as a prefix for the new methods.

    Methods that should be added in a webservice-specific implementation:
        - <name>_get_api_url(self, cnpj)
        - <name>_get_api_headers(self)
        - <name>_validate(self, response)
        - <name>_import_data(self, data)
    """

    _name = "l10n_br_cnpj_search.webservice.abstract"
    _description = "CNPJ Webservice"

    @api.model
    def get_provider(self):
        """Return selected provider in config"""
        if (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_br_cnpj_search.cnpj_provider")
        ):
            return (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("l10n_br_cnpj_search.cnpj_provider")
            )
        else:
            return "receitaws"

    @api.model
    def get_api_url(self, cnpj):
        """Get webservice endpoint

        Params:
            cnpj (str): Partner CNPJ.
        """
        if hasattr(self, "%s_get_api_url" % self.get_provider()):
            return getattr(self, "%s_get_api_url" % self.get_provider())(cnpj)
        return False

    @api.model
    def get_headers(self):
        """Get webservice request headers"""
        if hasattr(self, "%s_get_headers" % self.get_provider()):
            return getattr(self, "%s_get_headers" % self.get_provider())()
        return False

    @api.model
    def validate(self, response):
        """Validate webservice response.

        Returns: data (dict)
        """
        if hasattr(self, "%s_validate" % self.get_provider()):
            return getattr(self, "%s_validate" % self.get_provider())(response)
        return False

    @api.model
    def import_data(self, data):
        """Import webservice response to Odoo

        Params:
            data (dict): data with webservice response

        Returns:
            values (dict): dict with res_partner fields and it's values
        """
        if hasattr(self, "_%s_import_data" % self.get_provider()):
            return getattr(self, "_%s_import_data" % self.get_provider())(data)
        return False

    @api.model
    def get_data(self, data, name, title=False, lower=False):
        value = False
        if data.get(name) != "":
            value = data[name]
            if lower:
                value = value.lower()
            elif title:
                value = value.title()

        return value

    @api.model
    def _get_cnpj_param(self, param_name):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_br_cnpj_search." + param_name)
        )

    @api.model
    def _validate(self, response):
        if response.status_code != 200:
            raise ValidationError(_("%s") % response.reason)

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
