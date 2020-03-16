# Copyright (C) 2009  Renato Lima - Akretion
# Copyright (C) 2012  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'l10n_br_fiscal.document.mixin']

    @api.multi
    @api.depends('order_line.price_unit', 'order_line.tax_id',
                 'order_line.discount', 'order_line.product_uom_qty')
    def _amount_all_wrapper(self):
        """ Wrapper because of direct method passing
        as parameter for function fields """
        return self._amount_all()

    @api.multi
    def _amount_all(self):
        for order in self:
            order.amount_untaxed = 0.0
            order.amount_tax = 0.0
            order.amount_total = 0.0
            order.amount_discount = 0.0
            order.amount_gross = 0.0
            amount_tax = amount_untaxed = \
                amount_discount = amount_gross = 0.0
            for line in order.order_line:
                amount_tax += self._amount_line_tax(line)
                amount_untaxed += line.price_subtotal
                amount_discount += line.discount_value
                amount_gross += line.price_gross

            order.amount_tax = order.pricelist_id.currency_id.round(
                amount_tax)
            order.amount_untaxed = order.pricelist_id.currency_id.round(
                amount_untaxed)
            order.amount_total = (order.amount_untaxed +
                                  order.amount_tax)
            order.amount_discount = order.pricelist_id.currency_id.round(
                amount_discount)
            order.amount_gross = order.pricelist_id.currency_id.round(
                amount_gross)

    @api.model
    def _amount_line_tax(self, line):
        value = 0.0
        price = line._calc_line_base_price()
        qty = line._calc_line_quantity()
        for computed in line.tax_id.compute_all(
                price, quantity=qty, product=line.product_id,
                partner=line.order_id.partner_invoice_id)['taxes']:
            tax = self.env['account.tax'].browse(computed['id'])
            if not tax.tax_group_id.fiscal_tax_group_id.tax_include:
                value += computed.get('amount', 0.0)
        return value

    copy_note = fields.Boolean(
        string='Copiar Observação no documentos fiscal')

    amount_discount = fields.Float(
        compute='_amount_all_wrapper',
        string='Desconto (-)',
        digits=dp.get_precision('Account'),
        store=True,
        help="The discount amount.")

    amount_gross = fields.Float(
        compute='_amount_all_wrapper',
        string='Vlr. Bruto',
        digits=dp.get_precision('Account'),
        store=True, help="The discount amount.")

    discount_rate = fields.Float(
        string='Desconto',
        readonly=True,
        states={'draft': [('readonly', False)]})

    cnpj_cpf = fields.Char(
        string=u'CNPJ/CPF',
        related='partner_id.cnpj_cpf')

    legal_name = fields.Char(
        string=u'Razão Social',
        related='partner_id.legal_name')

    ie = fields.Char(
        string=u'Inscrição Estadual',
        related='partner_id.inscr_est')

    @api.onchange('discount_rate')
    def onchange_discount_rate(self):
        for sale_order in self:
            for sale_line in sale_order.order_line:
                sale_line.discount = sale_order.discount_rate

    # TODO FIscal Comment
    # @api.model
    # def _fiscal_comment(self, order):
    #     fp_comment = []
    #     fp_ids = []
    #
    #     for line in order.order_line:
    #         if line.operation_line_id and \
    #                 line.operation_line_id.inv_copy_note and \
    #                 line.operation_line_id.note:
    #             if line.operation_line_id.id not in fp_ids:
    #                 fp_comment.append(line.operation_line_id.note)
    #                 fp_ids.append(line.operation_line_id.id)
    #
    #      return fp_comment

    @api.multi
    def _prepare_invoice(self):
        self.ensure_one()
        result = super(SaleOrder, self)._prepare_invoice()
        context = self.env.context

        if (context.get('fiscal_type') == 'service' and
                self.order_line and self.order_line[0].operation_id):
            operation_id = self.order_line[0].operation_id.id
            result['operation_id'] = self.order_line.operation_id.id
        else:
            operation_id = self.operation_id
            result['operation_id'] = self.operation_id.id

        # TODO check journal
        # if operation_id:
        #    result['journal_id'] = operation_id.property_journal.id

        result['partner_shipping_id'] = self.partner_shipping_id.id

        comment = []
        if self.note and self.copy_note:
            comment.append(self.note)

        # TODO FISCAL Commnet
        # fiscal_comment = self._fiscal_comment(self)
        result['comment'] = " - ".join(comment)
        # result['fiscal_comment'] = " - ".join(fiscal_comment)
        result['operation_id'] = operation_id.id

        return result
