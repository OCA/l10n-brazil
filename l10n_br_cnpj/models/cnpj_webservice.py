# Copyright 2022 KMEE - Luis Felipe Mileo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class CNPJWebservice(models.Model):
    """Each specific webservice can extend the model by adding
    its own methods, using the webservice name (same as selection in config)
    as a prefix for the new methods.

    Methods that should be added in a webservice-specific implementation:
        - <name>_get_api_url(self)
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

    def get_api_url(self):
        """ Get webservice endpoint """
        if hasattr(self, "%s_get_api_url" % self.get_provider()):
            return getattr(self, "%s_get_api_url" % self.get_provider())()
        return False

    def import_data(self, data):
        """ Import webservice response to Odoo """
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
