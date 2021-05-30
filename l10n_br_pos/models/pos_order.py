# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time

from satcomum.ersat import ChaveCFeSAT

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_compare
from odoo.addons.l10n_br_pos.models.pos_config import \
    SIMPLIFIED_INVOICE_TYPE
from odoo.tools.translate import _


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

    num_sessao_sat = fields.Char('Número Sessão SAT envio Cfe')

    pos_order_associated = fields.Many2one('pos.order', 'Venda Associada')

    canceled_order = fields.Boolean('Venda Cancelada', readonly=True)

    cfe_cancelamento_return = fields.Binary('Retorno Cfe Cancelamento')

    chave_cfe_cancelamento = fields.Char('Chave da Cfe Cancelamento')

    num_sessao_sat_cancelamento = fields.Char(
        'Número Sessão SAT Cancelamento'
    )

    cnpj_cpf = fields.Char(
        string='CNPJ/CPF',
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
        pos_config = order.session_id.config_id
        if pos_config.iface_sat_via_proxy:
            sequence = pos_config.sequence_id
            cfe = ChaveCFeSAT(vals['chave_cfe'])
            order.name = sequence._interpolate_value("%s / %s" % (
                cfe.numero_serie,
                cfe.numero_cupom_fiscal,
            ))
        order.simplified_limit_check()
        return order

    @api.model
    def _process_order(self, order):
        order_id = super(PosOrder, self)._process_order(order)
        order_id = self.browse(order_id)
        for statement in order_id.statement_ids:
            if statement.journal_id.sat_payment_mode == '05' and statement.journal_id.pagamento_funcionarios:
                order_id.partner_id.credit_funcionario -= statement.amount
            elif statement.journal_id.sat_payment_mode == "05":
                order_id.partner_id.credit_limit -= statement.amount
        return order_id.id

    @api.multi
    def create_picking(self):
        super(PosOrder, self).create_picking()
        fiscal_category = self.session_id.config_id.fiscal_operation_id
        self.picking_id.fiscal_operation_id = \
            fiscal_category.id
        obj_fp_rule = self.env['account.fiscal.position.rule']
        kwargs = {
            'partner_id': self.picking_id.company_id.partner_id.id,
            'partner_shipping_id': self.picking_id.company_id.partner_id.id,
            'fiscal_operation_id': fiscal_category.id,
            'company_id': self.picking_id.company_id.id,
        }
        self.picking_id.fiscal_position = obj_fp_rule.apply_fiscal_mapping(
            {'value': {}}, **kwargs
        )['value']['fiscal_position']
        return True

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
                'total': '%.2f' % order.amount_total,
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

            for statement in order.statement_ids:
                if statement.journal_id.sat_payment_mode == "05":
                    order.partner_id.credit_limit += statement.amount

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
                'name': order.name + ' CANCEL',
                'pos_reference': order.pos_reference + ' CANCEL',
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

            statements = self.env['account.bank.statement.line']

            for statement in order.statement_ids:
                vals = {
                    'name': statement.display_name + " CANCEL",
                    'statement_id': statement.statement_id.id,
                    'ref': statement.ref,
                    'pos_statement_id': clone.id,
                    'journal_id': statement.journal_id.id,
                    'amount': statement.amount * -1,
                    'date': statement.date,
                    'partner_id': statement.partner_id.id
                    if statement.partner_id else False,
                    'account_id': statement.account_id.id
                }

                statements.create(vals)

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
            'doc_destinatario': order.partner_id.cnpj_cpf if order.partner_id
            else False,
            'xml_cfe_cacelada': order.cfe_cancelamento_return,
            'xml_cfe_venda': order.cfe_return,
            'canceled_order': order.canceled_order,
        }

        return dados_reimpressao


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    @api.multi
    def _buscar_produtos_devolvidos(self):
        for record in self:
            if record.order_id.chave_cfe:
                rel_documentos = self.env[
                    'l10n_br_account_product.document.related'].search(
                    [
                        ('access_key', '=', record.order_id.chave_cfe[3:])
                    ]
                )
                qtd_devolvidas = 0
                for documento in rel_documentos:
                    if documento.invoice_id.state in ('open', 'sefaz_export'):
                        for line in documento.invoice_id.invoice_line:
                            if record.product_id == line.product_id:
                                qtd_devolvidas += line.quantity
                record.qtd_produtos_devolvidos = qtd_devolvidas

    qtd_produtos_devolvidos = fields.Integer(
        string="Quantidade devolvida",
        compute=_buscar_produtos_devolvidos
    )
