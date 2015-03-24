# -*- encoding: utf-8 -*-
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

from openerp.exceptions import except_orm
from openerp import models, fields, api


class StockInvoiceOnShipping(models.TransientModel):
    _inherit = 'stock.invoice.onshipping'

    fiscal_category_journal = fields.Boolean(
        string=u"Diário da Categoria Fiscal", default=True)

    def create_invoice(self, cr, uid, ids, context=None):
        onshipdata_obj = self.read(
            cr, uid, ids, ['journal_id', 'group', 'invoice_date',
            'fiscal_category_journal'])
        res = super(StockInvoiceOnShipping, self).create_invoice(
            cr, uid, ids, context)

        if not res or not onshipdata_obj[0]['fiscal_category_journal']:
            return res

        if context is None:
            context = {}

        for inv in self.pool.get('account.invoice').browse(
            cr, uid, res.values(), context=context):
            journal_id = inv.fiscal_category_id and \
            inv.fiscal_category_id.property_journal
            if not journal_id:
                raise orm.except_orm(
                    _('Invalid Journal!'),
                    _('There is not journal defined for this company: %s in \
                    fiscal operation: %s !') % (inv.company_id.name,
                                                inv.fiscal_category_id.name))

            self.pool.get('account.invoice').write(
                cr, uid, inv.id, {'journal_id': journal_id.id},
                context=context)
        return res
