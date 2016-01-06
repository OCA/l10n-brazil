# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright (C) 2014  Renato Lima - Akretion
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

from openerp import models, api, _
from openerp.exceptions import Warning as UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _prepare_invoice(self, order, lines):
        result = super(SaleOrder, self)._prepare_invoice(order, lines)
        result['fiscal_type'] = self.env.context.get('fiscal_type')
        return result

    @api.model
    def _make_invoice(self, order, lines):

        context = dict(self.env.context)
        obj_invoice_line = self.env['account.invoice.line']
        lines_service = []
        lines_product = []
        inv_id_product = 0
        inv_id_service = 0

        def call_make_invoice(self, lines):
            self = self.with_context(context)
            return super(SaleOrder, self)._make_invoice(order, lines)

        if not order.fiscal_category_id.property_journal:
            raise UserError(
                _('Error !'),
                _("There is no journal defined for this company in Fiscal "
                    "Category: %s Company: %s") % (
                        order.fiscal_category_id.name, order.company_id.name))

        for inv_line in obj_invoice_line.browse(lines):
            if inv_line.product_id.fiscal_type == 'service':
                lines_service.append(inv_line.id)
            elif inv_line.product_id.fiscal_type == 'product':
                lines_product.append(inv_line.id)

        if lines_product:
            context['fiscal_type'] = 'product'
            inv_id_product = call_make_invoice(self, lines_product)

        if lines_service:
            context['fiscal_type'] = 'service'
            inv_id_service = call_make_invoice(self, lines_service)

        if inv_id_product and inv_id_service:
            self._cr.execute(
                'insert into sale_order_invoice_rel '
                '(order_id,invoice_id) values (%s,%s)', (
                    order.id, inv_id_service))

        inv_id = inv_id_product or inv_id_service

        return inv_id
