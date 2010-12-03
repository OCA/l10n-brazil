# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
# Copyright (C) 2010  Renato Lima - Akretion                                    #
#                                                                               #
#This program is free software: you can redistribute it and/or modify           #
#it under the terms of the GNU General Public License as published by           #
#the Free Software Foundation, either version 3 of the License, or              #
#(at your option) any later version.                                            #
#                                                                               #
#This program is distributed in the hope that it will be useful,                #
#but WITHOUT ANY WARRANTY; without even the implied warranty of                 #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                  #
#GNU General Public License for more details.                                   #
#                                                                               #
#You should have received a copy of the GNU General Public License              #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.          #
#################################################################################

from osv import fields,osv

class delivery_carrier(osv.osv):
    _inherit = "delivery.carrier"

    _columns = {
        'antt_code': fields.char('Codigo ANTT', size=32),
        'vehicle_ids': fields.one2many('l10n_br_delivery.carrier.vehicle', 'carrier_id', 'Vehicles'),
    }

delivery_carrier()

class l10n_br_delivery_carrier_vehicle(osv.osv):    
    
    _name = 'l10n_br_delivery.carrier.vehicle'
    _description = 'Veiculos das transportadoras'
    
    _columns = {
        'name': fields.char('Nome', size=32),
        'description': fields.char('Descrição', size=132),
        'plate': fields.char('Placa', size=7),
        'driver': fields.char('Condudor', size=64),
        'antt_code': fields.char('Codigo ANTT', size=32),
        'country_id': fields.many2one('res.country', 'País'),
        'state_id': fields.many2one('res.country.state', 'Estado', domain="[('country_id','=',country_id)]"),
        'city_id': fields.many2one('l10n_br_base.city', 'Municipio', domain="[('state_id','=',state_id)]"),
        'active': fields.boolean('Ativo'),
        'manufacture_year': fields.char('Ano de Fabricação', size=4),
        'model_year': fields.char('Ano do Modelo', size=4),
        'type': fields.selection([('bau','Caminhão Baú')], 'Ano do Modelo'),
        'carrier_id': fields.many2one('delivery.carrier', 'Carrier', select=True, required=True, ondelete='cascade'),        
    }

l10n_br_delivery_carrier_vehicle()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

