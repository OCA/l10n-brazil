# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class MDFeSeguroCarga(spec_models.SpecModel):
    _name = "l10n_br_mdfe.seguro.carga"
    _inherit = "mdfe.30.seg"
    _description = "Informações de Seguro na Carga MDFE"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_infResp = fields.Many2one(comodel_name="res.partner")

    mdfe30_infSeg = fields.Many2one(
        comodel_name="res.partner",
        domain=[
            ("is_company", "=", True),
            ("cnpj_cpf", "!=", False),
        ],
    )
