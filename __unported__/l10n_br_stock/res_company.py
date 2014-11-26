# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2011  Renato Lima - Akretion                                  #
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


class res_company(orm.Model):
    _inherit = 'res.company'
    _columns = {
        'stock_fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category',
            u'Categoria Fiscal Padrão Estoque'),
        'stock_in_fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category',
            u'Categoria Fiscal Padrão de Entrada',
            domain="[('journal_type', 'in', ('sale_refund', 'purchase')), "
            "('fiscal_type', '=', 'product'), ('type', '=', 'input')]"),
        'stock_out_fiscal_category_id': fields.many2one(
            'l10n_br_account.fiscal.category',
            u'Categoria Fiscal Padrão Saída',
            domain="[('journal_type', 'in', ('purchase_refund', 'sale')), "
            "('fiscal_type', '=', 'product'), ('type', '=', 'output')]"),
    }
