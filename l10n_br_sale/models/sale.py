# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright (C) 2009  Renato Lima - Akretion
# Copyright (C) 2012  Raphaël Valyi - Akretion
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

from openerp import models, fields, api
from openerp.addons import decimal_precision as dp


class SaleOrder(models.Model):
    _inherit = 'sale.order'

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
                price, qty, line.product_id.id,
                line.order_id.partner_invoice_id.id,
                fiscal_position=line.fiscal_position)['taxes']:
            tax = self.env['account.tax'].browse(computed['id'])
            if not tax.tax_code_id.tax_discount:
                value += computed.get('amount', 0.0)
        return value

    def _invoiced_rate(self, cursor, user, ids, name, arg, context=None):
        result = {}
        for sale in self.browse(cursor, user, ids, context=context):
            if sale.invoiced:
                result[sale.id] = 100.0
                continue
            tot = 0.0
            for invoice in sale.invoice_ids:
                if invoice.state not in ('draft', 'cancel') and \
                        invoice.fiscal_category_id.id == \
                        sale.fiscal_category_id.id:
                    tot += invoice.amount_untaxed
            if tot:
                result[sale.id] = min(100.0, tot * 100.0 / (
                    sale.amount_untaxed or 1.00))
            else:
                result[sale.id] = 0.0
        return result

    @api.model
    @api.returns('l10n_br_account.fiscal_category')
    def _default_fiscal_category(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        return company.sale_fiscal_category_id

    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Categoria Fiscal',
        domain="""[('type', '=', 'output'), ('journal_type', '=', 'sale'),
        ('state', '=', 'approved')]""",
        readonly=True, states={'draft': [('readonly', False)]},
        default=_default_fiscal_category)
    fiscal_position = fields.Many2one(
        'account.fiscal.position', 'Fiscal Position',
        domain="[('fiscal_category_id', '=', fiscal_category_id)]",
        readonly=True, states={'draft': [('readonly', False)]})
    invoiced_rate = fields.Float(compute='_invoiced_rate', string='Invoiced')
    copy_note = fields.Boolean(u'Copiar Observação no documentos fiscal')
    amount_untaxed = fields.Float(
        compute='_amount_all_wrapper', string='Untaxed Amount',
        digits=dp.get_precision('Account'), store=True,
        help="The amount without tax.", track_visibility='always')
    amount_tax = fields.Float(
        compute='_amount_all_wrapper', string='Taxes', store=True,
        digits=dp.get_precision('Account'), help="The tax amount.")
    amount_total = fields.Float(
        compute='_amount_all_wrapper', string='Total', store=True,
        digits=dp.get_precision('Account'), help="The total amount.")
    amount_discount = fields.Float(
        compute='_amount_all_wrapper', string='Desconto (-)',
        digits=dp.get_precision('Account'), store=True,
        help="The discount amount.")
    amount_gross = fields.Float(
        compute='_amount_all_wrapper', string='Vlr. Bruto',
        digits=dp.get_precision('Account'),
        store=True, help="The discount amount.")
    discount_rate = fields.Float(
        'Desconto', readonly=True, states={'draft': [('readonly', False)]})
    cnpj_cpf = fields.Char(
        string=u'CNPJ/CPF',
        related='partner_id.cnpj_cpf',
    )
    legal_name = fields.Char(
        string=u'Razão Social',
        related='partner_id.legal_name',
    )
    ie = fields.Char(
        string=u'Inscrição Estadual',
        related='partner_id.inscr_est',
    )

    @api.model
    def _fiscal_position_map(self, result, **kwargs):
        ctx = dict(self.env.context)
        if not kwargs.get('fiscal_category_id'):
            kwargs['fiscal_category_id'] = ctx.get('fiscal_category_id')
        ctx.update({
            'use_domain': ('use_sale', '=', True),
            'fiscal_category_id': ctx.get('fiscal_category_id')})
        return self.env['account.fiscal.position.rule'].with_context(
            ctx).apply_fiscal_mapping(result, **kwargs)

    @api.onchange('discount_rate')
    def onchange_discount_rate(self):
        for sale_order in self:
            for sale_line in sale_order.order_line:
                sale_line.discount = sale_order.discount_rate

    @api.onchange('fiscal_category_id')
    def onchange_fiscal(self):
        """Método chamado ao mudar a categoria fiscal
        para refinir a posição fiscal de acordo com as
        regras de posição fiscal"""
        if self.company_id and self.partner_id and self.fiscal_category_id:
            result = {'value': {'fiscal_position': False}}
            kwargs = {
                'partner_id': self.partner_id.id,
                'partner_invoice_id': self.partner_invoice_id.id,
                'fiscal_category_id': self.fiscal_category_id.id,
                'company_id': self.company_id.id,
                'context': self.env.context
            }
            result = self.env[
                'account.fiscal.position.rule'].apply_fiscal_mapping(
                    result, **kwargs)
            self.fiscal_position = result['value'].get('fiscal_position')

    @api.model
    def _fiscal_comment(self, order):
        fp_comment = []
        fp_ids = []

        for line in order.order_line:
            if line.fiscal_position and \
                    line.fiscal_position.inv_copy_note and \
                    line.fiscal_position.note:
                if line.fiscal_position.id not in fp_ids:
                    fp_comment.append(line.fiscal_position.note)
                    fp_ids.append(line.fiscal_position.id)

        return fp_comment

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
        context = self.env.context

        inv_lines = self.env['account.invoice.line'].browse(lines)

        if (context.get('fiscal_type') == 'service' and
                inv_lines and inv_lines[0].fiscal_category_id):
            fiscal_category_id = inv_lines[0].fiscal_category_id.id
            result['fiscal_position'] = inv_lines[0].fiscal_position.id
        else:
            fiscal_category_id = order.fiscal_category_id.id

        if fiscal_category_id:
            fiscal_category = self.env[
                'l10n_br_account.fiscal.category'].browse(fiscal_category_id)
            if fiscal_category:
                result['journal_id'] = fiscal_category[0].property_journal.id

        result['partner_shipping_id'] = order.partner_shipping_id.id

        comment = []
        if order.note and order.copy_note:
            comment.append(order.note)

        fiscal_comment = self._fiscal_comment(order)
        result['comment'] = " - ".join(comment)
        result['fiscal_comment'] = " - ".join(fiscal_comment)
        result['fiscal_category_id'] = fiscal_category_id

        return result


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _calc_line_base_price(self):
        return self.price_unit * (1 - (self.discount or 0.0) / 100.0)

    def _calc_line_quantity(self):
        return self.product_uom_qty

    def _calc_price_gross(self, qty):
        return self.price_unit * qty

    @api.one
    @api.depends('price_unit', 'tax_id', 'discount', 'product_uom_qty')
    def _amount_line(self):
        price = self._calc_line_base_price()
        qty = self._calc_line_quantity()
        taxes = self.tax_id.compute_all(price,
                                        qty,
                                        self.product_id.id,
                                        self.order_id.partner_invoice_id.id,
                                        fiscal_position=self.fiscal_position)

        self.price_subtotal = self.order_id.pricelist_id.currency_id.round(
            taxes['total'])
        self.price_gross = self._calc_price_gross(qty)
        self.discount_value = self.order_id.pricelist_id.currency_id.round(
            self.price_gross - (price * qty))

    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Categoria Fiscal',
        domain="[('type', '=', 'output'), ('journal_type', '=', 'sale')]",
        readonly=True, states={'draft': [('readonly', False)],
                               'sent': [('readonly', False)]})
    fiscal_position = fields.Many2one(
        'account.fiscal.position', 'Fiscal Position',
        domain="[('fiscal_category_id','=',fiscal_category_id)]",
        readonly=True, states={'draft': [('readonly', False)],
                               'sent': [('readonly', False)]})
    discount_value = fields.Float(compute='_amount_line',
                                  string='Vlr. Desc. (-)',
                                  digits=dp.get_precision('Sale Price'))
    price_gross = fields.Float(
        compute='_amount_line', string='Vlr. Bruto',
        digits=dp.get_precision('Sale Price'))
    price_subtotal = fields.Float(
        compute='_amount_line', string='Subtotal',
        digits=dp.get_precision('Sale Price'))

    @api.model
    def _fiscal_position_map(self, result, **kwargs):
        context = dict(self.env.context)
        context.update({'use_domain': ('use_sale', '=', True)})
        fp_rule_obj = self.env['account.fiscal.position.rule']

        partner_invoice = self.env['res.partner'].browse(
            kwargs.get('partner_invoice_id'))

        product_fc_id = fp_rule_obj.with_context(
            context).product_fiscal_category_map(
                kwargs.get('product_id'),
                kwargs.get('fiscal_category_id'),
                partner_invoice.state_id.id)

        if product_fc_id:
            kwargs['fiscal_category_id'] = product_fc_id

        result['value']['fiscal_category_id'] = kwargs.get(
            'fiscal_category_id')

        result.update(fp_rule_obj.with_context(context).apply_fiscal_mapping(
            result, **kwargs))
        fiscal_position = result['value'].get('fiscal_position')
        product_id = kwargs.get('product_id')

        if product_id and fiscal_position:
            obj_fposition = self.env['account.fiscal.position'].browse(
                fiscal_position)
            obj_product = self.env['product.product'].browse(product_id)
            context.update({
                'fiscal_type': obj_product.fiscal_type,
                'type_tax_use': 'sale', 'product_id': product_id})
            taxes = obj_product.taxes_id
            tax_ids = obj_fposition.with_context(context).map_tax(taxes)
            result['value']['tax_id'] = tax_ids

        return result

    @api.multi
    def product_id_change(self,  pricelist, product, qty=0,
                          uom=False, qty_uos=0, uos=False, name='',
                          partner_id=False, lang=False, update_tax=True,
                          date_order=False, packaging=False,
                          fiscal_position=False, flag=False):
        context = dict(self.env.context)
        self = self.with_context(context)
        parent_fiscal_category_id = context.get('parent_fiscal_category_id')
        company_id = context.get('company_id')
        partner_invoice_id = context.get('partner_invoice_id')
        result = {'value': {}}
        if parent_fiscal_category_id and product and partner_invoice_id \
                and company_id:
            kwargs = {
                'company_id': company_id,
                'partner_id': partner_id,
                'product_id': product,
                'partner_invoice_id': partner_invoice_id,
                'fiscal_category_id': parent_fiscal_category_id,
                'context': context
            }
            result.update(self._fiscal_position_map(result, **kwargs))
            if result['value'].get('fiscal_position'):
                fiscal_position = result['value'].get('fiscal_position')

            obj_product = self.env['product.product'].browse(product)
            context.update({'fiscal_type': obj_product.fiscal_type,
                            'type_tax_use': 'sale', 'product_id': product})

        result_super = super(SaleOrderLine, self).product_id_change(
            pricelist, product, qty, uom, qty_uos, uos, name, partner_id,
            lang, update_tax, date_order, packaging, fiscal_position, flag)
        result_super['value'].update(result['value'])
        return result_super

    @api.onchange('fiscal_category_id', 'fiscal_position')
    def onchange_fiscal(self):
        if self.order_id.company_id and self.order_id.partner_id \
                and self.fiscal_category_id:
            result = {'value': {}}
            kwargs = {
                'company_id': self.order_id.company_id.id,
                'partner_id': self.order_id.partner_id.id,
                'partner_invoice_id': self.order_id.partner_invoice_id.id,
                'product_id': self.product_id.id,
                'fiscal_category_id': self.fiscal_category_id.id,
                'context': self.env.context
            }
            result = self.env[
                'account.fiscal.position.rule'].apply_fiscal_mapping(
                    result, **kwargs)
            self.fiscal_category_id = result['value'].get(
                'fiscal_category_id', self.fiscal_category_id.id)
            self.fiscal_position = result['value'].get('fiscal_position')
            self.tax_ids = result['value'].get('tax_id')

    @api.model
    def _prepare_order_line_invoice_line(self, line, account_id=False):
        result = super(SaleOrderLine, self)._prepare_order_line_invoice_line(
            line, account_id)
        result['fiscal_category_id'] = line.fiscal_category_id.id or \
            line.order_id.fiscal_category_id.id or False
        result['fiscal_position'] = line.fiscal_position.id or \
            line.order_id.fiscal_position.id or False
        return result
