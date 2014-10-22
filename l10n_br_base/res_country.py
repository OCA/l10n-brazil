# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion                                  #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU Affero General Public License for more details.                          #
#                                                                             #
#You should have received a copy of the GNU Affero General Public License     #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
###############################################################################

from openerp.osv import orm, fields


class ResCountry(orm.Model):
    _inherit = 'res.country'
    _columns = {
        'bc_code': fields.char('Codigo BC', size=5),
        'ibge_code': fields.char('Codigo IBGE', size=5),
        'siscomex_code': fields.char('Codigo Siscomex', size=4)
    }


class ResCountryState(orm.Model):
    _inherit = 'res.country.state'
    _columns = {
        'ibge_code': fields.char('Cód. IBGE', size=2)
    }
