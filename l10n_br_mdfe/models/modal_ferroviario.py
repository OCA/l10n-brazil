# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields
from odoo.exceptions import UserError

from odoo.addons.spec_driven_model.models import spec_models


class MDFeModalFerroviario(spec_models.StackedModel):
    _name = "l10n_br_mdfe.modal.ferroviario"
    _inherit = "mdfe.30.ferrov"
    _description = "Modal Ferroviário MDFe"

    _mdfe30_odoo_module = (
        "odoo.addons.l10n_br_mdfe_spec.models.v3_0.mdfe_modal_ferroviario_v3_00"
    )
    _mdfe30_binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_modal_ferroviario_v3_00"
    _mdfe30_stacking_mixin = "mdfe.30.ferrov"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_xPref = fields.Char(related="document_id.mdfe30_xPref")

    mdfe30_dhTrem = fields.Datetime(related="document_id.mdfe30_dhTrem")

    mdfe30_xOri = fields.Char(related="document_id.mdfe30_xOri")

    mdfe30_xDest = fields.Char(related="document_id.mdfe30_xDest")

    mdfe30_qVag = fields.Char(related="document_id.mdfe30_qVag")

    mdfe30_vag = fields.One2many(related="document_id.mdfe30_vag")


class MDFeModalFerroviarioVagao(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.ferroviario.vagao"
    _inherit = "mdfe.30.vag"
    _description = "Informações do Vagão no Modal Ferroviário MDFe"
    _mdfe30_binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_modal_ferroviario_v3_00"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_pesoBC = fields.Float(required=True)

    mdfe30_pesoR = fields.Float(required=True)

    mdfe30_serie = fields.Char(required=True)

    mdfe30_nVag = fields.Char(required=True)

    mdfe30_TU = fields.Char(required=True)

    @api.constrains("mdfe30_serie")
    def check_serie(self):
        for _record in self.filtered(
            lambda v: v.mdfe30_serie and len(v.mdfe30_serie) != 3
        ):
            raise UserError(_("Wagon serie must have exactly 3 digits."))

    @api.constrains("mdfe30_tpVag")
    def check_tp_vag(self):
        for _record in self.filtered(
            lambda v: v.mdfe30_serie and len(v.mdfe30_tpVag) != 3
        ):
            raise UserError(_("Wagon type must have exactly 3 digits."))
