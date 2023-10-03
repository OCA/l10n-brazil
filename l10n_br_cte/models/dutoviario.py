# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class Dutoviario(spec_models.StackedModel):
    _name = "l10n_br_cte.modal.dutoviario"
    _inherit = "cte.40.duto"
    _stacked = "cte.40.duto"
    _binding_module = "nfelib.cte.bindings.v4_0.cte_modal_dutoviario_v4_00"
    _field_prefix = "cte40_"
    _schema_name = "cte"
    _schema_version = "4.0.0"
    _odoo_module = "l10n_br_cte"
    _spec_module = "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_modal_dutoviario_v4_00"
    _spec_tab_name = "CTe"
    _description = "Modal Dutoviario CTe"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    cte40_dIni = fields.Date(related="document_id.pipeline_initial_date")

    cte40_dFim = fields.Date(related="document_id.pipeline_final_date")

    cte40_vTar = fields.Float(related="document_id.pipeline_fare_value")

    def _prepare_dacte_values(self):
        if not self:
            return {}
