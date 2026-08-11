# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class CTeComment(spec_models.StackedModel):
    _name = "l10n_br_fiscal.comment"
    _inherit = ["l10n_br_fiscal.comment", "cte.40.tcte_obscont", "cte.40.tcte_obsfisco"]

    _cte40_odoo_module = (
        "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_tipos_basico_v4_00"
    )
    _cte40_stacking_mixin = "cte.40.tcte_obscont"
    _cte40_stacking_skip_paths = ("cte40_ObsCont_compl_id", "cte40_ObsFisco_compl_id")

    cte40_xCampo = fields.Char()

    cte40_xTexto = fields.Text()

    def _export_field(self, xsd_field, class_obj, member_spec, export_value=None):
        if xsd_field == "cte40_xCampo":
            return self.name[:20].strip()
        if xsd_field == "cte40_xTexto":
            if "doc" in self.env.context:
                doc_id = self.env.context["doc"]
                doc = self.env["l10n_br_fiscal.document"].browse(doc_id)
                vals = {"user": self.env.user, "ctx": self._context, "doc": doc}
                message = self.compute_message(vals).strip()
                if self.comment_type == "fiscal":
                    return message[:60]
                return message[:160]
        return super()._export_field(xsd_field, class_obj, member_spec, export_value)
