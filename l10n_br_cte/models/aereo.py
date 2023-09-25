# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from nfelib.cte.bindings.v4_0.cte_modal_aquaviario_v4_00 import Aquav

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models


class Aereo(spec_models.SpecModel):
    _name = "l10n_br_cte.modal.aereo"
    _inherit = "cte.40.aereo"

    cte40_dPrevAereo = fields.Date(
        string="Data prevista da entrega",
        help="Data prevista da entrega\nFormato AAAA-MM-DD",
        store="True",
    )

    cte40_natCarga = fields.One2many(
        related="document_id.fiscal_line_ids",
    )

    cte40_tarifa = fields.Many2one(comodel_name="l10n_br_cte.modal.aereo.tarifa")


class Tarifa(spec_models.SpecModel):
    _name = "l10n_br_cte.modal.aereo.tarifa"
    _inherit = "cte.40.tarifa"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    cte40_CL = fields.Selection(
        string="Classe",
        selection=[
            ("M", "Tarifa Mínima"),
            ("G", "Tarifa Geral"),
            ("E", "Tarifa Específica"),
        ],
        store=True,
        default="G",
    )

    cte40_vTar = fields.Monetary(currency_field="brl_currency_id")

    @api.model
    def export_fields(self):
        if len(self) > 1:
            return self.export_fields_multi()

        return Aquav.Tarifa(CL=self.cte40_CL, vTar=self.cte40_vTar)

    @api.model
    def export_fields_multi(self):
        return [record.export_fields() for record in self]
