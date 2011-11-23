# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
# Copyright (C) 2010  Renato Lima - Akretion                                    #
#                                                                               #
#This program is free software: you can redistribute it and/or modify           #
#it under the terms of the GNU Affero General Public License as published by    #
#the Free Software Foundation, either version 3 of the License, or              #
#(at your option) any later version.                                            #
#                                                                               #
#This program is distributed in the hope that it will be useful,                #
#but WITHOUT ANY WARRANTY; without even the implied warranty of                 #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                  #
#GNU Affero General Public License for more details.                            #
#                                                                               #
#You should have received a copy of the GNU Affero General Public License       #
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

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
