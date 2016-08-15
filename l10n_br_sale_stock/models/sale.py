# -*- coding: utf-8 -*-
# Copyright (C) 2013  Raphaël Valyi - Akretion                                #
# Copyright (C) 2014  Renato Lima - Akretion                                  #
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _prepare_invoice(self, order, lines):
        """Prepare the dict of values to create the new invoice for a
           sale order. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record order: sale.order record to invoice
           :param list(int) line: list of invoice line IDs that must be
                                  attached to the invoice
           :return: dict of value to create() the invoice
        """
        result = super(SaleOrder, self)._prepare_invoice(order, lines)

        if order.incoterm:
            result['incoterm'] = order.incoterm.id

        return result
