# Copyright 2022 KMEE - Luis Felipe Mileo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import ValidationError


class CNPJWebservice(models.Model):
    """Each specific webservice can extend the model by adding
    its own methods, using the webservice name (same as selection in config)
    as a prefix for the new methods.

    Methods that should be added in a webservice-specific implementation:
        - <name>_get_api_url(self, cnpj)
        - <name>_get_api_headers(self)
        - <name>_validate(self, response)
        - <name>_import_data(self, data)
    """

    _name = "l10n_br_cnpj.webservice"
    _description = "CNPJ Webservice"

    def get_provider(self):
        """ Return selected provider in config """
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_br_cnpj.cnpj_provider")
        )

    def get_api_url(self, cnpj):
        """Get webservice endpoint

        Params:
            cnpj (str): Partner CNPJ.
        """
        if hasattr(self, "%s_get_api_url" % self.get_provider()):
            return getattr(self, "%s_get_api_url" % self.get_provider())(cnpj)
        return False

    def get_headers(self):
        """ Get webservice request headers """
        if hasattr(self, "%s_get_headers" % self.get_provider()):
            return getattr(self, "%s_get_headers" % self.get_provider())()
        return False

    def validate(self, response):
        """Validate webservice response.

        Returns: data (dict)
        """
        if hasattr(self, "%s_validate" % self.get_provider()):
            return getattr(self, "%s_validate" % self.get_provider())(response)
        return False

    def import_data(self, data):
        """Import webservice response to Odoo

        Params:
            data (dict): data with webservice response

        Returns:
            values (dict): dict with res_partner fields and it's values
        """
        if hasattr(self, "%s_import_data" % self.get_provider()):
            return getattr(self, "%s_import_data" % self.get_provider())(data)
        return False

    @staticmethod
    def get_data(data, name, title=False, lower=False):
        value = False
        if data.get(name) != "":
            value = data[name]
            if lower:
                value = value.lower()
            elif title:
                value = value.title()

        return value

    def _get_cnpj_param(self, param_name):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_br_cnpj." + param_name)
        )

    @staticmethod
    def _validate(response):
        if response.status_code != 200:
            raise ValidationError(_("%s" % response.reason))
