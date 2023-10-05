# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class Rodoviario(spec_models.StackedModel):
    _name = "l10n_br_cte.modal.rodoviario"
    _inherit = "cte.40.rodo"
    _stacked = "cte.40.rodo"
    _binding_module = "nfelib.cte.bindings.v4_0.cte_modal_rodoviario_v4_00"
    _field_prefix = "cte40_"
    _schema_name = "cte"
    _schema_version = "4.0.0"
    _odoo_module = "l10n_br_cte"
    _spec_module = "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_modal_rodoviario_v4_00"
    _spec_tab_name = "CTe"
    _description = "Modal Rodoviario CTe"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    cte40_RNTRC = fields.Char(related="document_id.cte40_RNTRC")

    cte40_occ = fields.One2many(related="document_id.cte40_occ")


class Occ(spec_models.SpecModel):
    _name = "l10n_br_cte.modal.rodoviario.occ"
    _inherit = "cte.40.occ"
    _binding_module = "nfelib.cte.bindings.v4_0.cte_modal_rodoviario_v4_00"
    _description = "Ordens de Coleta associados"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    cte40_serie = fields.Char(string="Série da OCC")

    cte40_nOcc = fields.Char(string="Número da Ordem de coleta")

    cte40_dEmi = fields.Date(
        string="Data de emissão da ordem de coleta",
        help="Data de emissão da ordem de coleta\nFormato AAAA-MM-DD",
    )

    cte40_emiOcc = fields.Many2one(comodel_name="res.partner", string="emiOcc")
