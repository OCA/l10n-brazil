# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models

from ..constants.modal import TUF


class Rodo(spec_models.StackedModel):
    _name = "l10n_br_cte.modal.rodo"
    _inherit = "cte.40.rodo"
    _description = "Modal Rodoviario CTe"

    _cte40_stacking_mixin = "cte.40.rodo"
    _cte40_odoo_module = (
        "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_modal_rodoviario_v4_00"
    )
    _cte40_binding_module = "nfelib.cte.bindings.v4_0.cte_modal_rodoviario_v4_00"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    cte40_RNTRC = fields.Char(related="document_id.cte40_RNTRC")

    cte40_occ = fields.One2many(related="document_id.cte40_occ")


class Occ(spec_models.StackedModel):
    _name = "l10n_br_cte.modal.rodo.occ"
    _inherit = "cte.40.occ"
    _description = "Ordens de Coleta associados"

    _cte40_stacking_mixin = "cte.40.occ"
    _cte40_odoo_module = (
        "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_modal_rodoviario_v4_00"
    )
    _cte40_binding_module = "nfelib.cte.bindings.v4_0.cte_modal_rodoviario_v4_00"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    cte40_serie = fields.Char(string="Série da OCC")

    cte40_nOcc = fields.Char(string="Número da Ordem de coleta")

    cte40_dEmi = fields.Date(
        string="Data de emissão da ordem de coleta",
        help="Data de emissão da ordem de coleta\nFormato AAAA-MM-DD",
    )

    cte40_CNPJ = fields.Char(
        string="Número do CNPJ",
        help="Número do CNPJ\nInformar os zeros não significativos.",
    )

    cte40_cInt = fields.Char(
        string="Código interno de uso da transportadora",
        help=(
            "Código interno de uso da transportadora\nUso intermo das "
            "transportadoras."
        ),
    )

    cte40_IE = fields.Char(string="Inscrição Estadual")

    cte40_UF = fields.Selection(
        TUF,
        string="Sigla da UF",
        help="Sigla da UF\nInformar EX para operações com o exterior.",
    )

    cte40_fone = fields.Char(string="Telefone")
