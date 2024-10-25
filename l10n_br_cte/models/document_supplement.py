# Copyright 2023 KMEE (Luiz Felipe do Divino <luiz.divino@kmee.com.br>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class CTeSupplement(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document.supplement"
    _inherit = ["l10n_br_fiscal.document.supplement", "cte.40.tcte_infctesupl"]

    _cte40_odoo_module = (
        "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_tipos_basico_v4_00"
    )
    _cte40_stacking_mixin = "cte.40.tcte_infctesupl"

    cte40_qrCodCTe = fields.Char(related="qrcode")
