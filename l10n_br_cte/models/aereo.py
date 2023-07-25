# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class Aereo(spec_models.SpecModel):
    _name = "l10n_br_cte.aereo"
    _inherit = "cte.40.aereo"

    document_id = fields.One2many(
        comodel_name="l10n_br_fiscal.document", inverse_name="cte40_aereo"
    )

    cte40_dPrevAereo = fields.Date(related="dPrevAereo", store=True)

    dPrevAereo = fields.Date(
        string="Data prevista da entrega",
        help="Data prevista da entrega\nFormato AAAA-MM-DD",
        store="True",
    )

    cte40_natCarga = fields.One2many(
        related="document_id.fiscal_line_ids",
    )

    cte40_tarifa = fields.Many2one(comodel_name="l10n_br_cte.tarifa")

    def export_data(self):
        return {
            "cte40_dPrevAereo": self.cte40_dPrevAereo,
            "cte40_natCarga": {"cte40_xDime": self.cte40_natCarga.xDime},
            "cte40_tarifa": {
                "cte40_CL": self.cte40_tarifa.cte40_CL,
                "cte40_vTar": self.cte40_tarifa.cte40_vTar,
            },
        }


class Tarifa(spec_models.SpecModel):
    _name = "l10n_br_cte.tarifa"
    _inherit = "cte.40.tarifa"

    cte40_CL = fields.Selection(related="CL", store=True)

    CL = fields.Selection(
        string="Classe",
        selection=[
            ("M", "Tarifa Mínima"),
            ("G", "Tarifa Geral"),
            ("E", "Tarifa Específica"),
        ],
        store=True,
        default="G",
    )

    cte40_vTar = fields.Monetary(related="vTar")

    vTar = fields.Monetary(currency_field="brl_currency_id")
