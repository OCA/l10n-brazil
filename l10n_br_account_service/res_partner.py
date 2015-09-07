# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Renato Lima - Akretion                                  #
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

from openerp.osv import orm


class AccountFiscalPosition(orm.Model):
    _inherit = 'account.fiscal.position'

    def map_tax_code(self, cr, uid, product_id, fiscal_position,
                     company_id=False, tax_ids=False, context=None):
        if not context:
            context = {}

        result = {}
        if tax_ids:

            if context.get('type_tax_use') == 'sale':

                if company_id:
                    company = self.pool.get('res.company').browse(
                        cr, uid, company_id, context=context)

                    company_tax_def = company.service_tax_definition_line

                    for tax_def in company_tax_def:
                        if tax_def.tax_id.id in tax_ids and tax_def.tax_code_id:
                                result.update({tax_def.tax_id.domain:
                                               tax_def.tax_code_id.id})
        return result
