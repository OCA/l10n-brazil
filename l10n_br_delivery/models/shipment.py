# Copyright (C) 2010  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class DeliveryShipment(models.Model):
    _name = 'l10n_br_delivery.shipment'
    _description = 'Delivery Shipment'

    code = fields.Char(
        string='Name',
        size=32,
    )

    description = fields.Char(
        string='Description',
        size=132,
    )

    carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Carrier',
        index=True,
        required=True,
    )

    vehicle_id = fields.Many2one(
        comodel_name='l10n_br_delivery.carrier.vehicle',
        string='Vehicle',
        index=True,
        required=True,
    )

    volume = fields.Float(
        string='Volume',
    )

    carrier_tracking_ref = fields.Char(
        string='Carrier Tracking Ref',
        size=32,
    )

    number_of_packages = fields.Integer(
        string='Number of Packages',
    )
