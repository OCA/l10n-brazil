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

FISCAL_POSITION_COLUMNS = {
    'cfop_id': fields.many2one('l10n_br_account.cfop', 'CFOP'),
    'fiscal_category_id': fields.many2one('l10n_br_account.fiscal.category',
                                          'Categoria Fiscal'),
    'fiscal_category_type': fields.related(
        'fiscal_category_id', 'type', type='char', readonly=True,
        relation='l10n_br_account.fiscal.category', store=True, string='Type'),
    'fiscal_category_fiscal_type': fields.related(
        'fiscal_category_id', 'fiscal_type', type='char', readonly=True,
        relation='l10n_br_account.fiscal.category', store=True,
        string='Fiscal Type'),
    'refund_fiscal_category_id': fields.many2one(
        'l10n_br_account.fiscal.category', 'Categoria Fiscal de Devolução'),
    'inv_copy_note': fields.boolean('Copiar Observação na Nota Fiscal'),
    'asset_operation': fields.boolean('Operação de Aquisição de Ativo',
                                      help="Caso seja marcada essa opção,"
                                      " será incluido o IPI na base de "
                                      "calculo do ICMS.")}


class account_fiscal_position_template(osv.osv):
    _inherit = 'account.fiscal.position.template'
    _columns = FISCAL_POSITION_COLUMNS

account_fiscal_position_template()


class account_fiscal_position_tax_template(osv.osv):
    _inherit = 'account.fiscal.position.tax.template'

    _columns = {
        'tax_code_dest_id': fields.many2one('account.tax.code.template',
                                            'Replacement Tax')}

account_fiscal_position_tax_template()


class account_fiscal_position(osv.osv):
    _inherit = 'account.fiscal.position'
    _columns = FISCAL_POSITION_COLUMNS

account_fiscal_position()


class account_fiscal_position_tax(osv.osv):
    _inherit = 'account.fiscal.position.tax'
    _columns = {
        'tax_code_dest_id': fields.many2one('account.tax.code',
                                            'Replacement Tax')}

account_fiscal_position_tax()


class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = {
        'partner_fiscal_type_id': fields.many2one(
            'l10n_br_account.partner.fiscal.type',
            'Tipo Fiscal do Parceiro',
            domain="[('tipo_pessoa','=',tipo_pessoa)]")}

res_partner()
