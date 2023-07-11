# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.spec_driven_model.models import spec_models


class NFeRelated(spec_models.StackedModel):

    _name = "l10n_br_fiscal.document.related"
    _inherit = ["l10n_br_fiscal.document.related", "cte.40.tcte_infnfe"]
    _stacked = "cte.40.tcte_infnfe"
    _field_prefix = "cte40_"
    _schema_name = "cte"
    _schema_version = "4.0.0"
    _odoo_module = "l10n_br_cte"
    _spec_module = "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_tipos_basico_v4_00"
    _spec_tab_name = "CTe"
