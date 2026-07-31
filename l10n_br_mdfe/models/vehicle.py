# Copyright 2024 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from odoo.addons.l10n_br_mdfe_spec.models.v3_0.mdfe_modal_rodoviario_v3_00 import (
    VEICTRACAO_TPCAR,
    VEICTRACAO_TPROD,
)


class MDFeVehicle(models.Model):
    _name = "l10n_br_mdfe.vehicle"
    _description = "MDF-e Vehicle"
    _rec_name = "display_name"

    active = fields.Boolean(default=True)

    name = fields.Char(string="Nome do Veículo")

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Owner",
        required=True,
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        related="partner_id.company_id",
        store=True,
    )

    display_name = fields.Char(compute="_compute_display_name")

    mdfe30_cInt = fields.Char(string="Vehicle Code", size=10)

    mdfe30_placa = fields.Char(string="Plate", required=True)

    mdfe30_RENAVAM = fields.Char(string="RENAVAM", size=11)

    mdfe30_tara = fields.Char(string="Tara (KG)")

    mdfe30_capKG = fields.Char(string="Capacity (KG)")

    mdfe30_capM3 = fields.Char(string="Capacity (M3)")

    mdfe30_tpRod = fields.Selection(
        selection=VEICTRACAO_TPROD,
        string="Wheel Type",
    )

    mdfe30_tpCar = fields.Selection(
        selection=VEICTRACAO_TPCAR,
        string="Body Type",
    )

    rodo_vehicle_state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="UF",
        domain=[("country_id.code", "=", "BR")],
    )

    @api.depends("name", "mdfe30_placa", "mdfe30_cInt")
    def _compute_display_name(self):
        for rec in self:
            parts = []
            if rec.name:
                parts.append(rec.name)
            if rec.mdfe30_placa:
                parts.append(rec.mdfe30_placa)
            if rec.mdfe30_cInt:
                parts.append(rec.mdfe30_cInt)
            rec.display_name = " - ".join(parts) if parts else "Novo Veículo"

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if "partner_id" not in res or not res.get("partner_id"):
            company = self.env.company
            if company.partner_id:
                res["partner_id"] = company.partner_id.id
        return res
