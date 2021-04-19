# Copyright (C) 2010  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class L10nBrDeliveryCarrierVehicle(models.Model):
    _name = 'l10n_br_delivery.carrier.vehicle'
    _description = 'Veiculos das transportadoras'

    name = fields.Char('Nome', required=True, size=32)
    description = fields.Char(u'Descrição', size=132)
    plate = fields.Char('Placa', size=7)
    driver = fields.Char('Condudor', size=64)
    rntc_code = fields.Char('Codigo ANTT', size=32)
    country_id = fields.Many2one('res.country', 'País')
    state_id = fields.Many2one(
        'res.country.state', 'Estado',
        domain="[('country_id', '=', country_id)]")
    l10n_br_city_id = fields.Many2one(
        'res.city', 'Municipio',
        domain="[('state_id','=',state_id)]")
    active = fields.Boolean('Ativo')
    manufacture_year = fields.Char(u'Ano de Fabricação', size=4)
    model_year = fields.Char('Ano do Modelo', size=4)
    type = fields.Selection([('bau', u'Caminhão Baú')], 'Tipo do Modelo')
    carrier_id = fields.Many2one(
        'delivery.carrier', 'Carrier', index=True,
        required=True, ondelete='cascade')


class L10nBrDeliveryShipment(models.Model):
    _name = 'l10n_br_delivery.shipment'
    _description = 'Carga/Remessa/Transporte/?'

    code = fields.Char('Nome', size=32)
    description = fields.Char('Descrição', size=132)
    carrier_id = fields.Many2one(
        'delivery.carrier', 'Carrier', index=True, required=True)
    vehicle_id = fields.Many2one(
        'l10n_br_delivery.carrier.vehicle', 'Vehicle',
        index=True, required=True)
    volume = fields.Float('Volume')
    carrier_tracking_ref = fields.Char('Carrier Tracking Ref', size=32)
    number_of_packages = fields.Integer('Number of Packages')
