# Copyright 2023 KMEE (Luiz Felipe do Divino <luiz.divino@kmee.com.br>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class CTeSupplement(spec_models.SpecModel):
    _name = "l10n_br_fiscal.document.supplement"
    _inherit = ["l10n_br_fiscal.document.supplement", "cte.40.tcte_infctesupl"]
    _cte40_binding_type = "Tcte.InfCteSupl"  # avoid ambiguity with NFe and MDFe modules

    cte40_qrCodCTe = fields.Char(related="qrcode")
