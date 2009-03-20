# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import osv, fields
import pooler

class Country(osv.osv):
    """Country"""
    _name = 'res.country'
    _inherit = 'res.country'
    _columns = {
        'codigo_bc': fields.integer('Código BC', help='Código do país no Banco Central'),
        }
    _sql_constraints = [
        ('codigo_bc_uniq', 'unique (codigo_bc)', 'O Código do pais no Banco Central precisa ser único!')
    ]

Country()

class CountryState(osv.osv):
    """State"""
    _name = 'res.country.state'
    _inherit = 'res.country.state'
    _columns = {
        'codigo_ibge': fields.integer('Código IBGE', help='Código do estado no IBGE'),
        }
    _sql_constraints = [
        ('codigo_ibge_uniq', 'unique (codigo_ibge)', 'O Código do estado no IBGE precisa ser único!')
    ]
CountryState()

class CountryStateCity(osv.osv):
    """Cidade """
    _name = 'res.country.state.city'
    _columns = {
        'name': fields.char('Nome da cidade', size=30, required=True),
        'codigo_ibge': fields.integer('Código IBGE', help='Código da cidade no IBGE'),
        'state_id': fields.many2one('res.country.state', 'Estado', required=True),
        'country' : fields.related ('state_id','country_id',type='many2one', relation='res.country',string='País'),
    }
    _sql_constraints = [
        ('codigo_ibge_uniq', 'unique (codigo_ibge)', 'O Código da cidade no IBGE precisa ser único!')
    ]
CountryStateCity()

