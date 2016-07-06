# -*- coding: utf-8 -*-
# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time

from openerp import models, fields, api
from openerp.addons import decimal_precision as dp
from openerp.tools.float_utils import float_compare
from openerp.addons.l10n_br_pos.models.pos_config import \
    SIMPLIFIED_INVOICE_TYPE
from openerp.tools.translate import _


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def _order_fields(self, ui_order):
        return {
            'name':           ui_order['name'],
            'user_id':        ui_order['user_id'] or False,
            'session_id':     ui_order['pos_session_id'],
            'lines':          ui_order['lines'],
            'pos_reference':  ui_order['name'],
            'partner_id':     ui_order['partner_id'] or False,
            'cfe_return':     ui_order['cfe_return'],
            'num_sessao_sat': ui_order['num_sessao_sat'],
            'chave_cfe':      ui_order['chave_cfe'],
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

    num_sessao_sat = fields.Char(u'Número Sessão SAT envio Cfe')

    pos_order_associated = fields.Many2one('pos.order', 'Venda Associada')

    canceled_order = fields.Boolean('Venda Cancelada', readonly=True)

    cfe_cancelamento_return = fields.Binary('Retorno Cfe Cancelamento')

    chave_cfe_cancelamento = fields.Char('Chave da Cfe Cancelamento')

    num_sessao_sat_cancelamento = fields.Char(u'Número Sessão SAT Cancelamento')

    cnpj_cpf = fields.Char(
        string=u'CNPJ/CPF',
        related='partner_id.cnpj_cpf',
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

    @api.model
    def return_orders_from_session(self, **kwargs):
        orders_session = {'Orders': []}
        orders = self.search(
            [
                ('session_id', '=', kwargs['session_id']),
                ('state', '=', 'paid'),
                ('chave_cfe', '!=', '')
            ], limit=5, order="id DESC"
        )
        for order in orders:
            order_vals = {
                'id': order.id,
                'name': order.name,
                'pos_reference': order.pos_reference,
                'partner': order.partner_id.name,
                'date': order.date_order,
                'chave_cfe': order.chave_cfe,
                'canceled_order': order.canceled_order,
                'can_cancel': False,
            }
            orders_session['Orders'].append(order_vals)
            orders_session['Orders'][0]['can_cancel'] = True
        return orders_session

    @api.model
    def refund(self, ids, dados):
        """Create a copy of order  for refund order"""
        clone_list = []

        for order in self.browse(ids):
            current_session_ids = self.env['pos.session'].search([
                ('state', '!=', 'closed'),
                ('user_id', '=', self.env.uid)]
            )

            # if not current_session_ids:
            #     raise osv.except_osv(_('Error!'), _('To return product(s),
            # you need to open a session that will be used to register
            # the refund.'))

            clone_id = order.copy()

            clone_id.write({
                'name': order.name + ' REFUND',
                'pos_reference': order.pos_reference + ' REFUND',
                'session_id': current_session_ids.id,
                'date_order': time.strftime('%Y-%m-%d %H:%M:%S'),
                'pos_order_associated': order.id,
                'canceled_order': True,
                'chave_cfe': '',
                'cfe_return': '',
                'num_sessao_sat': ''
            })

            clone_list.append(clone_id.id)

        for clone in self.browse(clone_list):
            for order_line in clone.lines:
                order_line.write({
                    'qty': -order_line.qty
                })

            clone.action_paid()
            parent_order = self.browse(clone.pos_order_associated.id)
            parent_order.write({
                'canceled_order': True,
                'pos_order_associated': clone.id,
                'cfe_cancelamento_return': dados['xml'],
                'chave_cfe_cancelamento': dados['numSessao'],
                'num_sessao_sat_cancelamento': dados['chave_cfe'],
            })

        return True

    @api.model
    def retornar_order_by_id(self, order_id):
        order = self.browse(order_id)
        dados_reimpressao = {
            'order_id': order_id,
            'chaveConsulta': order.chave_cfe,
            'xml_cfe_cacelada': order.cfe_cancelamento_return,
            'xml_cfe_venda': order.cfe_return,
            'canceled_order': order.canceled_order,
        }

        return dados_reimpressao
