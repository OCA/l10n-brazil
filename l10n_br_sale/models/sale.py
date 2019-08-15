# -*- coding: utf-8 -*-
# Copyright (C) 2009  Renato Lima - Akretion
# Copyright (C) 2012  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


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
                price, quantity=qty, product=line.product_id,
                partner=line.order_id.partner_invoice_id)['taxes']:
            tax = self.env['account.tax'].browse(computed['id'])
            if not tax.tax_group_id.tax_discount:
                value += computed.get('amount', 0.0)
        return value

    @api.model
    def _default_fiscal_category(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        return company.sale_fiscal_category_id

    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Categoria Fiscal',
        domain="""[('type', '=', 'output'), ('journal_type', '=', 'sale'),
        ('state', '=', 'approved')]""",
        readonly=True, states={'draft': [('readonly', False)]},
        default=_default_fiscal_category)
    fiscal_position_id = fields.Many2one(
        domain="[('fiscal_category_id', '=', fiscal_category_id)]",
        readonly=True, states={'draft': [('readonly', False)]}
    )
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
    def _fiscal_position_map(self, **kwargs):
        ctx = dict(self.env.context)
        if not kwargs.get('fiscal_category_id'):
            kwargs['fiscal_category_id'] = ctx.get('fiscal_category_id')
        ctx.update({
            'use_domain': ('use_sale', '=', True),
            'fiscal_category_id': ctx.get('fiscal_category_id')})
        return self.env['account.fiscal.position.rule'].with_context(
            ctx).apply_fiscal_mapping(**kwargs)

    @api.onchange('discount_rate')
    def onchange_discount_rate(self):
        for sale_order in self:
            for sale_line in sale_order.order_line:
                sale_line.discount = sale_order.discount_rate

    @api.multi
    @api.onchange('fiscal_category_id', 'partner_invoice_id')
    def onchange_fiscal(self):
        """Método chamado ao mudar a categoria fiscal
        para refinir a posição fiscal de acordo com as
        regras de posição fiscal"""
        for record in self:
            if record.company_id and record.partner_id and\
                    record.fiscal_category_id:
                kwargs = {
                    'partner_id': record.partner_id,
                    'partner_invoice_id': record.partner_invoice_id,
                    'fiscal_category_id': record.fiscal_category_id,
                    'company_id': record.company_id,
                    'context': record.env.context
                }
                obj_fiscal_position = record.env[
                    'account.fiscal.position.rule'].apply_fiscal_mapping(
                    **kwargs
                )
                if obj_fiscal_position:
                    record.fiscal_position_id = obj_fiscal_position.id
                else:
                    record.fiscal_position_id = False

    @api.model
    def _fiscal_comment(self, order):
        fp_comment = []
        fp_ids = []

        for line in order.order_line:
            if line.fiscal_position_id and \
                    line.fiscal_position_id.inv_copy_note and \
                    line.fiscal_position_id.note:
                if line.fiscal_position_id.id not in fp_ids:
                    fp_comment.append(line.fiscal_position_id.note)
                    fp_ids.append(line.fiscal_position_id.id)

        return fp_comment

    @api.multi
    def _prepare_invoice(self):
        self.ensure_one()
        result = super(SaleOrder, self)._prepare_invoice()
        context = self.env.context

        if (context.get('fiscal_type') == 'service' and
                self.order_line and self.order_line[0].fiscal_category_id):
            fiscal_category_id = self.order_line[0].fiscal_category_id.id
            result['fiscal_position_id'] = self.order_line.fiscal_position.id
        else:
            fiscal_category_id = self.fiscal_category_id
            result['fiscal_position_id'] = self.fiscal_position_id.id

        if fiscal_category_id:
            result['journal_id'] = fiscal_category_id.property_journal.id

        result['partner_shipping_id'] = self.partner_shipping_id.id

        comment = []
        if self.note and self.copy_note:
            comment.append(self.note)

        fiscal_comment = self._fiscal_comment(self)
        result['comment'] = " - ".join(comment)
        result['fiscal_comment'] = " - ".join(fiscal_comment)
        result['fiscal_category_id'] = fiscal_category_id.id

        return result

    @api.multi
    @api.onchange('partner_shipping_id', 'partner_id')
    def onchange_partner_shipping_id(self):
        """
        Trigger the change of fiscal position when
        the shipping address is modified.
        """
        for record in self:
            super(SaleOrder, self).onchange_partner_shipping_id()
            record.onchange_fiscal()
        return {}
