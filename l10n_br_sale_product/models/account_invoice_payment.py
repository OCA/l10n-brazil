# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _


class AccountInvoicePayment(models.Model):

    _inherit = 'account.invoice.payment'

    sale_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        ondelete='set null',
    )

    def _set_parent(self, field_parent, field_parent_id):
        date = super(AccountInvoicePayment, self)._set_parent(
            field_parent, field_parent_id
        )
        if field_parent == 'sale_id':
            date = field_parent_id.date_order
            self.sale_id = field_parent_id
        return date
