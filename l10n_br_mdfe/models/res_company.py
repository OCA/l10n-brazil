# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.spec_driven_model.models import spec_models


class ResCompany(spec_models.SpecModel):

    _name = "res.company"
    _inherit = [
        "res.company",
        "mdfe.30.emi",
    ]
    _mdfe_search_keys = ["mdfe30_CNPJ", "mdfe30_xNome", "mdfe_xFant"]

    # TODO
