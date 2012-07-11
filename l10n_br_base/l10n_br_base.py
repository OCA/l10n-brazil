# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
# Copyright (C) 2009  Renato Lima - Akretion                                    #
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

from osv import osv, fields

class l10n_br_base_city(osv.osv):

    _name = 'l10n_br_base.city'
    _description = 'City with IBGE Codes'

    _columns = {
                'name': fields.char('Name', size=64, required=True),
                'state_id': fields.many2one('res.country.state', 'State', required=True),
                'ibge_code': fields.char('IBGE Code', size=7),
               }

l10n_br_base_city()

class l10n_br_base_zip(osv.osv):

    _name = 'l10n_br_base.zip'
    _rec_name = 'code'

    _columns = {
                'code': fields.char('ZIP', size=8, required=True),
                'street_type': fields.char('Type', size=26),
                'street': fields.char('Street', size=72),
                'district': fields.char('District', size=72),
                'country_id': fields.many2one('res.country', 'Country'),
                'state_id': fields.many2one("res.country.state", 'State', 
                                            domain="[('country_id','=',country_id)]"),
                'l10n_br_city_id': fields.many2one('l10n_br_base.city', 'City', 
                                                   required=True, domain="[('state_id','=',state_id)]"),
                }

l10n_br_base_zip()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
