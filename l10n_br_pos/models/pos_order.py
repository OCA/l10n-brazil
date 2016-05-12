# -*- coding: utf-8 -*-
# See README.rst file on addon root folder for license details

from openerp import models, fields, api
from openerp.addons import decimal_precision as dp
from openerp.tools.float_utils import float_compare
from openerp.addons.l10n_br_pos.models.pos_config import \
    SIMPLIFIED_INVOICE_TYPE


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def _pos_order_type(self):
        return SIMPLIFIED_INVOICE_TYPE + [('nfe', 'NF-E')]

    simplified = fields.Boolean(string='Simplified invoice', default=True)
    fiscal_document_type = fields.Selection(
        string='Fiscal Document Type',
        selection='_pos_order_type',
        states={'draft': [('readonly', False)]},
        readonly=True
    )

    @api.one
    def action_invoice(self):
        self.simplified = False
        self.fiscal_document_type = 'nfe'

    @api.multi
    def simplified_limit_check(self):
        for order in self:
            if not order.simplified:
                continue
            limit = order.session_id.config_id.simplified_invoice_limit
            amount_total = order.amount_total
            precision_digits = dp.get_precision('Account')(self.env.cr)[1]
            # -1 or 0: amount_total <= limit, simplified
            #       1: amount_total > limit, can not be simplified
            simplified = (
                float_compare(amount_total, limit,
                              precision_digits=precision_digits) <= 0)
            # Change simplified flag if incompatible
            if not simplified:
                order.write(
                    {'simplified': simplified,
                     'fiscal_document_type':
                         order.session_id.config_id.simplified_invoice_type
                     })

    @api.multi
    def write(self, vals):
        result = super(PosOrder, self).write(vals)
        self.simplified_limit_check()
        return result

    @api.model
    def create(self, vals):
        order = super(PosOrder, self).create(vals)
        order.simplified_limit_check()
        return order
