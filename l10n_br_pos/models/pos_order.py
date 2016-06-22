# -*- coding: utf-8 -*-
# See README.rst file on addon root folder for license details
import base64

from openerp import models, fields, api
from openerp.addons import decimal_precision as dp
from openerp.tools.float_utils import float_compare
from openerp.addons.l10n_br_pos.models.pos_config import \
    SIMPLIFIED_INVOICE_TYPE
from openerp import http


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def _order_fields(self, ui_order):
        return {
            'name':         ui_order['name'],
            'user_id':      ui_order['user_id'] or False,
            'session_id':   ui_order['pos_session_id'],
            'lines':        ui_order['lines'],
            'pos_reference':ui_order['name'],
            'partner_id':   ui_order['partner_id'] or False,
            'cfe_return':   ui_order['cfe_return'],
            'num_sessao_sat': ui_order['num_sessao_sat'],
            'chave_cfe':    ui_order['chave_cfe'],
        }

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

    cfe_return = fields.Binary('Retorno Cfe')

    chave_cfe = fields.Char('Chave da Cfe')

    num_sessao_sat = fields.Char(u'Número sessão SAT')

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

    @api.model
    def return_orders_from_session(self, **kwargs):
        orders_session = {'Orders': []}
        orders = self.search(
            [('session_id', '=', kwargs['session_id'])], limit=5, order="id"
        )
        orders = reversed(orders)
        for order in orders:
            order_vals = {
                'name': order.name,
                'pos_reference': order.pos_reference,
                'partner_id': order.partner_id.id,
                'date': order.date_order,
                'chave_cfe': order.chave_cfe,
                'can_cancel': False,
            }
            orders_session['Orders'].append(order_vals)
            orders_session['Orders'][0]['can_cancel'] = True
        return orders_session

    @api.model
    def cancel_last_order(self, **kwargs):
        order = self.search(
            [('chave_cfe', '=', kwargs['chave_cfe'])]
        )

        return self.cancel_order(order)
