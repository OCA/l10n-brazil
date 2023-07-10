# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class ResCompany(spec_models.SpecModel):

    _name = "res.company"
    _inherit = ["res.company", "cte.40.tcte_emit"]
    _cte_search_keys = ["cte40_CNPJ", "cte40_xNome", "cte40_xFant"]

    cte40_CNPJ = fields.Char(related="partner_id.cte40_CNPJ")
    cte40_CPF = fields.Char(related="partner_id.cte40_CPF")
