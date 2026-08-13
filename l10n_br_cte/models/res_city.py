# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ResCity(models.Model):
    _inherit = "res.city"
    _cte_search_keys = ["ibge_code"]

    # Creation during CTe import is prevented via the
    # spec_create_forbidden_models context key set by the import caller.
