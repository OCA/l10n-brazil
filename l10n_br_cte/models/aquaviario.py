# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class Aquav(spec_models.StackedModel):
    _name = "l10n_br_cte.modal.aquav"
    _inherit = "cte.40.aquav"
    _description = "Modal Aquaviário CTe"

    _cte40_stacking_mixin = "cte.40.aquav"
    _cte40_odoo_module = (
        "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_modal_aquaviario_v4_00"
    )
    _cte40_binding_module = "nfelib.cte.bindings.v4_0.cte_modal_aquaviario_v4_00"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    cte40_vAFRMM = fields.Monetary(related="document_id.cte40_vAFRMM")

    cte40_vPrest = fields.Monetary(
        related="document_id.cte40_vTPrest"
    )  # TODO: avaliar melhor

    cte40_xNavio = fields.Char(related="document_id.cte40_xNavio")

    cte40_nViag = fields.Char(related="document_id.cte40_nViag")

    cte40_direc = fields.Selection(related="document_id.cte40_direc")

    cte40_irin = fields.Char(related="document_id.cte40_irin")

    cte40_tpNav = fields.Selection(related="document_id.cte40_tpNav")

    cte40_balsa = fields.One2many(related="document_id.cte40_balsa")

    def _prepare_dacte_values(self):
        if not self:
            return {}


class Balsa(spec_models.SpecModel):
    _name = "l10n_br_cte.modal.aquav.balsa"
    _inherit = "cte.40.balsa"
    _description = "Grupo de informações das balsas"

    _cte40_stacking_mixin = "cte.40.balsa"
    _cte40_odoo_module = (
        "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_modal_aquaviario_v4_00"
    )
    _cte40_binding_module = "nfelib.cte.bindings.v4_0.cte_modal_aquaviario_v4_00"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    cte40_xBalsa = fields.Char(string="Identificador da Balsa")
