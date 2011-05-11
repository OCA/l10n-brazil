# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
# Copyright (C) 2009  Renato Lima - Akretion                                    #
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

from osv import osv, fields

#################################################################################
# Municipios e Códigos do IBGE
#################################################################################
class l10n_br_base_city(osv.osv):
    _name = 'l10n_br_base.city'
    _description = 'Municipios e Códigos do IBGE'
    _columns = {
        'name': fields.char('Nome', size=64, required=True),
        'state_id': fields.many2one('res.country.state', 'Estado', required=True),
        'ibge_code': fields.char('Codigo IBGE', size=7),
    }
l10n_br_base_city()

#################################################################################
# CEP - Código de endereçamento Postal
#################################################################################
class l10n_br_base_cep(osv.osv):
    _name = 'l10n_br_base.cep'
    _rec_name = 'code'
    _columns = {
        'code': fields.char('CEP', size=8, required=True),
        'street_type': fields.char('Tipo', size=26),
        'street': fields.char('Logradouro', size=72),
        'district': fields.char('Bairro', size=72),
        'state_id': fields.many2one('res.country.state', 'Estado', required=True),
        'l10n_br_city_id': fields.many2one('l10n_br_base.city', 'Cidade', required=True, domain="[('state_id','=',state_id)]"),
    }
l10n_br_base_cep()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
