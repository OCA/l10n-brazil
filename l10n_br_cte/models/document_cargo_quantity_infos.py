# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class CTeCargoQuantityInfos(spec_models.SpecModel):
    _name = "l10n_br_cte.cargo.quantity.infos"
    _inherit = "cte.40.tcte_infq"
    _description = "Informações de quantidades da Carga do CT-e"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    cte40_cUnid = fields.Selection(
        required=True,
    )

    cte40_tpMed = fields.Char(
        required=True,
    )

    cte40_qCarga = fields.Float(
        required=True,
    )
