# Copyright (C) 2026 Madooit
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class Document(models.Model):
    _inherit = "l10n_br_fiscal.document"

    vehicle_id = fields.Many2one(
        comodel_name="l10n_br_delivery.carrier.vehicle",
        string="Veículo",
    )

    @api.onchange("vehicle_id")
    def _onchange_vehicle_id(self):
        """Fill the MDF-e vehicle fields from the delivery vehicle registry."""
        if self.vehicle_id:
            vehicle = self.vehicle_id
            self.mdfe30_cInt = vehicle.vehicle_code
            self.mdfe30_placa = vehicle.plate
            self.mdfe30_RENAVAM = vehicle.renavam
            self.mdfe30_tara = vehicle.tara
            self.mdfe30_capKG = vehicle.capacity_kg
            self.mdfe30_capM3 = vehicle.capacity_m3
            self.mdfe30_tpRod = vehicle.wheel_type
            self.mdfe30_tpCar = vehicle.body_type
            self.rodo_vehicle_state_id = vehicle.state_id
