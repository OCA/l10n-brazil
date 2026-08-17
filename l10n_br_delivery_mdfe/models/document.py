# Copyright (C) 2026 Madooit
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.tools import float_repr


def _mdfe_measure(value):
    """Decimal string of a measure, as expected by the MDF-e schema."""
    return float_repr(value, 2) if value else False


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
            self.mdfe30_tara = _mdfe_measure(vehicle.tara)
            self.mdfe30_capKG = _mdfe_measure(vehicle.capacity_kg)
            self.mdfe30_capM3 = _mdfe_measure(vehicle.capacity_m3)
            self.mdfe30_tpRod = vehicle.wheel_type
            self.mdfe30_tpCar = vehicle.body_type
            self.rodo_vehicle_state_id = vehicle.state_id
