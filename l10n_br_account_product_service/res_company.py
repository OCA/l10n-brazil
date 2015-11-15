# -*- coding: utf-8 -*-
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


class ResCompany(orm.Model):
    _inherit = 'res.company'

    def _get_taxes(self, cr, uid, ids, name, arg, context=None):
        result = {}
        for company in self.browse(cr, uid, ids, context=context):
            result[company.id] = {'product_tax_ids': [],
                                  'service_tax_ids': []}
            product_tax_ids = [tax.tax_id.id for tax in
                               company.product_tax_definition_line]
            service_tax_ids = [tax.tax_id.id for tax in
                               company.service_tax_definition_line]
            product_tax_ids.sort()
            service_tax_ids.sort()
            result[company.id]['product_tax_ids'] = product_tax_ids
            result[company.id]['service_tax_ids'] = service_tax_ids
        return result

    _columns = {
        'product_tax_ids': fields.function(
            _get_taxes, method=True, type='many2many',
            relation='account.tax', string='Product Taxes', multi='all'),
        'service_tax_ids': fields.function(
            _get_taxes, method=True, type='many2many',
            relation='account.tax', string='Product Taxes', multi='all'),
    }