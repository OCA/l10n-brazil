# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields
from odoo.exceptions import UserError

from odoo.addons.spec_driven_model.models import spec_models


class MDFeModalFerroviario(spec_models.StackedModel):
    _name = "l10n_br_mdfe.modal.ferroviario"
    _inherit = "mdfe.30.ferrov"
    _stacked = "mdfe.30.ferrov"
    _binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_modal_ferroviario_v3_00"
    _field_prefix = "mdfe30_"
    _schema_name = "mdfe"
    _schema_version = "3.0.0"
    _odoo_module = "l10n_br_mdfe"
    _spec_module = (
        "odoo.addons.l10n_br_mdfe_spec.models.v3_0.mdfe_modal_ferroviario_v3_00"
    )
    _spec_tab_name = "MDFe"
    _description = "Modal Ferroviário MDFe"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_xPref = fields.Char(related="document_id.train_prefix")

    mdfe30_dhTrem = fields.Datetime(related="document_id.train_release_time")

    mdfe30_xOri = fields.Char(related="document_id.train_origin")

    mdfe30_xDest = fields.Char(related="document_id.train_destiny")

    mdfe30_qVag = fields.Char(related="document_id.train_wagon_quantity")

    mdfe30_vag = fields.One2many(related="document_id.train_wagon_ids")


class MDFeModalFerroviarioVagao(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.ferroviario.vagao"
    _inherit = "mdfe.30.vag"
    _binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_modal_ferroviario_v3_00"
    _description = "Informações do Vagão no Modal Ferroviário MDFe"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_pesoBC = fields.Float(required=True)

    mdfe30_pesoR = fields.Float(required=True)

    mdfe30_serie = fields.Char(required=True)

    mdfe30_nVag = fields.Char(required=True)

    mdfe30_TU = fields.Char(required=True)

    @api.constrains("mdfe30_serie")
    def check_serie(self):
        for _record in self.filtered(lambda v: len(v.mdfe30_serie) != 3):
            raise UserError(_("Wagon serie must have exactly 3 digits."))

    @api.constrains("mdfe30_tpVag")
    def check_tp_vag(self):
        for _record in self.filtered(lambda v: len(v.mdfe30_tpVag) != 3):
            raise UserError(_("Wagon type must have exactly 3 digits."))
