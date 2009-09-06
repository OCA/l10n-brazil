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
# Municipios e Cￃﾳdigos do IBGE
##############################################################################
class l10n_br_city(osv.osv):
    _name = 'l10n_br.city'
    _description = 'Municipios e Cￃﾳdigos do IBGE'
    _columns = {
        'name': fields.char('Nome', size=64, required=True),
        'state_id': fields.many2one('res.country.state', 'Estado', required=True),
        'ibge_code': fields.char('Codigo IBGE', size=7),
    }
l10n_br_city()

##############################################################################
# CEP - Cￃﾳdigo de endereￃﾧamento Postal
##############################################################################
class l10n_br_cep(osv.osv):
    _name = 'l10n_br.cep'
    _rec_name = 'code'
    _columns = {
        'city_id': fields.many2one('l10n_br.city', 'Municipio', required=True),
    }
l10n_br_cep()