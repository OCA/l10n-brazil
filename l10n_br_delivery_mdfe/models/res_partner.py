# Copyright (C) 2026 Madooit
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    vehicle_ids = fields.One2many(
        comodel_name="l10n_br_delivery.carrier.vehicle",
        inverse_name="owner_id",
        string="Veículos",
    )
