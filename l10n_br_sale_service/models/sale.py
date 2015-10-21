# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2014  Renato Lima - Akretion                                  #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

from openerp.osv import orm
from openerp.tools.translate import _
from openerp.addons import decimal_precision as dp


# TODO
class SaleOrder(orm.Model):
    _inherit = 'sale.order'

    def _make_invoice(self, cr, uid, order, lines, context=None):
        if context is None:
            context = {}
        obj_invoice_line = self.pool.get('account.invoice.line')
        lines_service = []
        lines_product = []
        inv_product_ids = []
        inv_service_ids = []
        inv_id_product = False
        inv_id_service = False

        if (order.fiscal_category_id and not
            (order
             .fiscal_category_id.property_journal)):
            raise orm.except_orm(
                    _('Error !'),
                    _("""There is no journal defined for this company in Fiscal
                    Category: %s Company: %s""") % (
                        order.fiscal_category_id.name, order.company_id.name))

        for inv_line in obj_invoice_line.browse(cr, uid, lines,
                                                context=context):
            if inv_line.product_id.fiscal_type == 'service':
                lines_service.append(inv_line.id)
            elif inv_line.product_id.fiscal_type == 'product':
                lines_product.append(inv_line.id)

        if lines_product:
            context['fiscal_type'] = 'product'
            inv_id_product = super(SaleOrder, self)._make_invoice(
                cr, uid, order, lines_product, context=context)
            inv_product_ids.append(inv_id_product)

        if lines_service:
            context['fiscal_type'] = 'service'
            inv_id_service = super(SaleOrder, self)._make_invoice(
                cr, uid, order, lines_service, context=context)
            inv_service_ids.append(inv_id_service)

        return inv_id_product or inv_id_service
