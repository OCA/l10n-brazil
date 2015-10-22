# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2010  Renato Lima - Akretion                                  #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

from openerp import models, fields


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
        'l10n_br_base.city', 'Municipio',
        domain="[('state_id','=',state_id)]")
    active = fields.Boolean('Ativo')
    manufacture_year = fields.Char(u'Ano de Fabricação', size=4)
    model_year = fields.Char('Ano do Modelo', size=4)
    type = fields.Selection([('bau', u'Caminhão Baú')], 'Ano do Modelo')
    carrier_id = fields.Many2one(
        'delivery.carrier', 'Carrier', select=True,
        required=True, ondelete='cascade')


class L10nBrDeliveryShipment(models.Model):
    _name = 'l10n_br_delivery.shipment'

    code = fields.Char('Nome', size=32)
    description = fields.Char('Descrição', size=132)
    carrier_id = fields.Many2one(
        'delivery.carrier', 'Carrier', select=True, required=True)
    vehicle_id = fields.Many2one(
        'l10n_br_delivery.carrier.vehicle', 'Vehicle',
        select=True, required=True)
    volume = fields.Float('Volume')
    carrier_tracking_ref = fields.Char('Carrier Tracking Ref', size=32)
    number_of_packages = fields.Integer('Number of Packages')

    def _cal_weight(self, cr, uid, ids, name, args, context=None):
        result = {}

        for picking in self.browse(cr, uid, ids, context):
            total_weight = total_weight_net = 0.00

            for move in picking.move_lines:
                total_weight += move.weight
                total_weight_net += move.weight_net

            result[picking.id] = {
                'weight': total_weight,
                'weight_net': total_weight_net,
            }

        return result

    def _get_picking_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('stock.move').browse(cr, uid, ids,
                                                       context=context):
            result[line.picking_id.id] = True
        return list(result.keys())
