# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.spec_driven_model.models import spec_models


class ResPartner(spec_models.SpecModel):

    _name = "res.partner"
    _inherit = [
        "res.partner",
        "mdfe.30.tendereco",
        "mdfe.30.tlocal",
        "mdfe.30.tendeemi",
        "mdfe.30.dest",
        "mdfe.30.tresptec",
        "mdfe.30.autxml",
    ]
    _mdfe_search_keys = ["mdfe30_CNPJ", "mdfe30_CPF", "mdfe_xNome"]

    # TODO
