# Copyright 2025 Akretion (Raphaël Valyi <raphael.valyi@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ResCountryState(models.Model):
    _inherit = "res.country.state"
    _mdfe_search_keys = ["ibge_code", "code"]
    _mdfe_extra_domain = [("ibge_code", "!=", False)]

    # Creation during MDFe import is prevented via the
    # spec_create_forbidden_models context key set by the import caller.
