# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel               #
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

from osv import osv, fields


class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = {
        'partner_fiscal_type_id': fields.many2one(
            'l10n_br_account.partner.fiscal.type',
            'Tipo Fiscal do Parceiro',
            domain="[('tipo_pessoa','=',tipo_pessoa)]")}

res_partner()


class account_fiscal_position_template(osv.osv):
    _inherit = 'account.fiscal.position.template'
    _columns = {
        'fiscal_operation_id': fields.many2one(
            'l10n_br_account.fiscal.operation', 'Operação Fiscal')}

account_fiscal_position_template()


class account_fiscal_position(osv.osv):
    _inherit = 'account.fiscal.position'
    _columns = {
        'fiscal_operation_id': fields.many2one(
            'l10n_br_account.fiscal.category', 'Categoria Fiscal'),
        'cfop_id': fields.many2one('l10n_br_account.cfop', 'CFOP')}

account_fiscal_position()
