# -*- coding: utf-8 -*-
# Copyright (C) 2010  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    antt_code = fields.Char(
        'Codigo ANTT',
        size=32)

    vehicle_ids = fields.One2many(
        'l10n_br_delivery.carrier.vehicle',
        'carrier_id', u'Veículos')
