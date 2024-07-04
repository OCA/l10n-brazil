# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class CTeComment(spec_models.StackedModel):

    _name = "l10n_br_fiscal.comment"
    _inherit = ["l10n_br_fiscal.comment", "cte.40.tcte_obscont", "cte.40.tcte_obsfisco"]
    _stacked = "cte.40.tcte_obscont"
    _field_prefix = "cte40_"
    _schema_name = "cte"
    _schema_version = "4.0.0"
    _odoo_module = "l10n_br_cte"
    _spec_module = "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_tipos_basico_v4_00"
    _spec_tab_name = "CTe"
    _stacking_points = {}
    _stack_skip = ("cte40_ObsCont_compl_id", "cte40_ObsFisco_compl_id")
    _binding_module = "nfelib.cte.bindings.v4_0.cte_tipos_basico_v4_00"

    cte40_xCampo = fields.Char()

    cte40_xTexto = fields.Text()

    def _export_field(self, xsd_field, class_obj, member_spec, export_value=None):
        if xsd_field == "cte40_xCampo":
            return self.name[:20].strip()
        if xsd_field == "cte40_xTexto":
            # Aparentemente isso terá que ser feito de outra forma
            if (
                "active_id" in self.env.context
                and self.env.context.get("active_model")
                == "l10n_br_fiscal.document.line"
            ):
                active_id = self.env.context["active_id"]
                doc = self.env["l10n_br_fiscal.document"].browse(active_id)
                vals = {"user": self.env.user, "ctx": self._context, "doc": doc}
                message = self.compute_message(vals).strip()
                if self.comment_type == "fiscal":
                    return message[:60]
                return message[:160]
        return super()._export_field(xsd_field, class_obj, member_spec, export_value)
