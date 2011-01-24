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

##############################################################################
# Empresa Personalizada
##############################################################################
class res_company(osv.osv):
    _inherit = "res.company"
    _columns = {
        'fiscal_type': fields.selection([('1', 'Simples Nacional'), ('2', 'Simples Nacional – excesso de sublimite de receita bruta'), ('3', 'Regime Normal')], 'Regime Tributário', required=True)
    }
    _defaults = {
        'fiscal_type': '3',
    }

res_company()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
