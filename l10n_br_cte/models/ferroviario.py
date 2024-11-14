# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models


class Ferrov(spec_models.StackedModel):
    _name = "l10n_br_cte.modal.ferrov"
    _inherit = "cte.40.ferrov"
    _description = "Modal Ferroviario CTe"

    _cte40_stacking_mixin = "cte.40.ferrov"
    _cte40_odoo_module = (
        "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_modal_ferroviario_v4_00"
    )
    _cte40_binding_module = "nfelib.cte.bindings.v4_0.cte_modal_ferroviario_v4_00"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    cte40_tpTraf = fields.Selection(related="document_id.cte40_tpTraf")

    cte40_fluxo = fields.Char(related="document_id.cte40_fluxo")

    cte40_vFrete = fields.Monetary(
        related="document_id.cte40_vFrete", currency_field="currency_id"
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        default=lambda self: self.env.company.currency_id,
    )

    cte40_chCTeFerroOrigem = fields.Char(related="document_id.cte40_chCTeFerroOrigem")

    cte40_respFat = fields.Selection(related="document_id.cte40_respFat")

    cte40_ferrEmi = fields.Selection(related="document_id.cte40_ferrEmi")

    cte40_ferroEnv = fields.One2many(compute="_compute_railroad")

    @api.depends("document_id.cte40_ferroEnv")
    def _compute_railroad(self):
        for record in self:
            record.cte40_ferroEnv = [(6, 0, record.document_id.cte40_ferroEnv.ids)]

    def _prepare_dacte_values(self):
        if not self:
            return {}
