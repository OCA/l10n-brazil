# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class MDFeModalAereo(spec_models.StackedModel):
    _name = "l10n_br_mdfe.modal.aereo"
    _inherit = "mdfe.30.aereo"
    _description = "Modal Aereo MDFe"

    _mdfe30_odoo_module = (
        "odoo.addons.l10n_br_mdfe_spec.models.v3_0.mdfe_modal_aereo_v3_00"
    )
    _mdfe30_binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_modal_aereo_v3_00"
    _mdfe30_stacking_mixin = "mdfe.30.aereo"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_nac = fields.Char(related="document_id.mdfe30_nac")

    mdfe30_matr = fields.Char(related="document_id.mdfe30_matr")

    mdfe30_nVoo = fields.Char(related="document_id.mdfe30_nVoo")

    mdfe30_dVoo = fields.Date(related="document_id.mdfe30_dVoo")

    mdfe30_cAerEmb = fields.Char(related="document_id.mdfe30_cAerEmb")

    mdfe30_cAerDes = fields.Char(related="document_id.mdfe30_cAerDes")
