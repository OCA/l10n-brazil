# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from osv import osv, fields

##############################################################################
# País Personalizado
##############################################################################
class res_country(osv.osv):
    _description = 'País Personalizado'
    _inherit = 'res.country'
    _columns = {
        'bc_code': fields.char('Cód. BC', size=5),
    }
country()

##############################################################################
# Estado Personalizado
##############################################################################
class res_country_state(osv.osv):
    _description = 'Estado Personalizado'
    _inherit = 'res.country.state'
    _columns = {
        'ibge_code': fields.char('Cód. IBGE', size=2),
    }
res_country_state()
