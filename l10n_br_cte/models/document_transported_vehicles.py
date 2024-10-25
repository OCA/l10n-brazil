# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class CTeCargoQuantityInfos(spec_models.SpecModel):
    _name = "l10n_br_cte.transported.vehicles"
    _inherit = "cte.40.veicnovos"
    _description = "Informações dos veículos transportados"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="document_id.company_id.currency_id",
    )

    cte40_chassi = fields.Char(string="Chassi do veículo", required=True, size=17)

    cte40_cCor = fields.Char(string="Cor do veículo", required=True, size=4)

    cte40_xCor = fields.Char(string="Descrição da cor", required=True)

    cte40_cMod = fields.Char(
        string="Código Marca Modelo",
        required=True,
    )

    cte40_vUnit = fields.Monetary(
        string="Valor Unitário do Veículo",
        required=True,
        currency_field="currency_id",
    )

    cte40_vFrete = fields.Monetary(
        string="Frete Unitário",
        required=True,
        currency_field="currency_id",
    )
