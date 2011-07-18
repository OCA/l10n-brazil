# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel                 #
#                                                                               #
#This program is free software: you can redistribute it and/or modify           #
#it under the terms of the GNU Affero General Public License as published by    #
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
# Parceiro Personalizado
##############################################################################
class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = {
        'partner_fiscal_type_id': fields.many2one('l10n_br_account.partner.fiscal.type', 'Tipo Fiscal do Parceiro', domain="[('tipo_pessoa','=',tipo_pessoa)]"),
    }
res_partner()

##############################################################################
# Posição Fiscal Personalizada
##############################################################################
class account_fiscal_position(osv.osv):
    _inherit = 'account.fiscal.position'
    _columns = {
                'fiscal_operation_id': fields.many2one('l10n_br_account.fiscal.operation', 'Operação Fiscal'),
                }
        
account_fiscal_position()

class account_fiscal_position_tax(osv.osv):
    
    _inherit = 'account.fiscal.position.tax'

account_fiscal_position_tax()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
