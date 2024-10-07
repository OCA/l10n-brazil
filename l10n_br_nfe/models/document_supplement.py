# Copyright 2023 KMEE (Felipe Zago Rodrigues <felipe.zago@kmee.com.br>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo.addons.spec_driven_model.models import spec_models


class NFeSupplement(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document.supplement"
    _description = "NFe Supplement Document"
    _inherit = "nfe.40.infnfesupl"
    _nfe40_spec_settings = {
        "module": "odoo.addons.l10n_br_nfe_spec.models.v4_0.leiaute_nfe_v4_00",
        "stacking_mixin": "nfe.40.infnfesupl",
        "stacking_points": {},
    }
