# -*- coding: utf-8 -*-
# Copyright (C) 2014  Renato Lima - Akretion                                  #
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api
from openerp import _
from openerp.exceptions import ValidationError

from openerp.addons import decimal_precision as dp
from openerp.addons.l10n_br_base.tools.misc import calc_price_ratio


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    @api.depends('order_line.price_unit', 'order_line.tax_id',
                 'order_line.discount', 'order_line.product_uom_qty',
                 'order_line.freight_value', 'order_line.insurance_value',
                 'order_line.other_costs_value')
    def _amount_all_wrapper(self):
        """
        Wrapper because of direct method passing as parameter
        for function fields
        """
        return self._amount_all()

    @api.multi
    def _amount_all(self):
        for order in self:
            order.amount_untaxed = 0.0
            order.amount_tax = 0.0
            order.amount_total = 0.0
            order.amount_extra = 0.0
            order.amount_discount = 0.0
            order.amount_gross = 0.0

            amount_tax = amount_untaxed = \
                amount_discount = amount_gross = \
                amount_extra = 0.0
            for line in order.order_line:
                amount_tax += self._amount_line_tax(line)
                amount_extra += (line.insurance_value +
                                 line.freight_value +
                                 line.other_costs_value)
                amount_untaxed += line.price_subtotal
                amount_discount += line.discount_value
                amount_gross += line.price_gross

            order.amount_tax = order.pricelist_id.currency_id.round(
                amount_tax)
            order.amount_untaxed = order.pricelist_id.currency_id.round(
                amount_untaxed)
            order.amount_extra = order.pricelist_id.currency_id.round(
                amount_extra)
            order.amount_total = (order.amount_untaxed +
                                  order.amount_tax +
                                  order.amount_extra)
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
                price,
                qty,
                partner=line.order_id.partner_invoice_id,
                product=line.product_id,
                # line.order_id.partner_id,
                fiscal_position=line.fiscal_position,
                insurance_value=line.insurance_value,
                freight_value=line.freight_value,
                other_costs_value=line.other_costs_value)['taxes']:
            tax = self.env['account.tax'].browse(computed['id'])
            if not tax.tax_code_id.tax_discount:
                value += computed.get('amount', 0.0)
        return value

    @api.model
    def _default_ind_pres(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        return company.default_ind_pres

    @api.one
    def _get_costs_value(self):
        """ Read the l10n_br specific functional fields. """
        freight = costs = insurance = 0.0
        for line in self.order_line:
            freight += line.freight_value
            insurance += line.insurance_value
            costs += line.other_costs_value
        self.amount_freight = freight
        self.amount_costs = costs
        self.amount_insurance = insurance

    @api.one
    def _set_amount_freight(self):
        for line in self.order_line:
            if not self.amount_gross:
                break
            line.write({
                'freight_value': calc_price_ratio(
                    line.price_gross,
                    self.amount_freight,
                    line.order_id.amount_gross),
                })
        return True

    @api.one
    def _set_amount_insurance(self):
        for line in self.order_line:
            if not self.amount_gross:
                break
            line.write({
                'insurance_value': calc_price_ratio(
                    line.price_gross,
                    self.amount_insurance,
                    line.order_id.amount_gross),
                })
        return True

    @api.one
    def _set_amount_costs(self):
        for line in self.order_line:
            if not self.amount_gross:
                break
            line.write({
                'other_costs_value': calc_price_ratio(
                    line.price_gross,
                    self.amount_costs,
                    line.order_id.amount_gross),
                })
        return True

    ind_pres = fields.Selection([
        ('0', u'Não se aplica (por exemplo,'
              u' Nota Fiscal complementar ou de ajuste)'),
        ('1', u'Operação presencial'),
        ('2', u'Operação não presencial, pela Internet'),
        ('3', u'Operação não presencial, Teleatendimento'),
        ('4', u'NFC-e em operação com entrega em domicílio'),
        ('5', u'Operação presencial, fora do estabelecimento'),
        ('9', u'Operação não presencial, outros')
    ], u'Tipo de operação', readonly=True,
        states={'draft': [('readonly', False)]}, required=False,
        help=u'Indicador de presença do comprador no estabelecimento \
             comercial no momento da operação.', default=_default_ind_pres)
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
    amount_extra = fields.Float(
        compute='_amount_all_wrapper', string='Extra',
        digits=dp.get_precision('Account'), store=True,
        help="The total amount.")
    amount_discount = fields.Float(
        compute='_amount_all_wrapper', string='Desconto (-)',
        digits=dp.get_precision('Account'), store=True,
        help="The discount amount.")
    amount_gross = fields.Float(
        compute='_amount_all_wrapper', string='Vlr. Bruto',
        digits=dp.get_precision('Account'),
        store=True, help="The discount amount.")
    amount_freight = fields.Float(
        compute=_get_costs_value, inverse=_set_amount_freight,
        string='Frete', default=0.00, digits=dp.get_precision('Account'),
        readonly=True, states={'draft': [('readonly', False)]})
    amount_costs = fields.Float(
        compute=_get_costs_value, inverse=_set_amount_costs,
        string='Outros Custos', default=0.00,
        digits=dp.get_precision('Account'),
        readonly=True, states={'draft': [('readonly', False)]})
    amount_insurance = fields.Float(
        compute=_get_costs_value, inverse=_set_amount_insurance,
        string='Seguro', default=0.00, digits=dp.get_precision('Account'),
        readonly=True, states={'draft': [('readonly', False)]})
    account_payment_ids = fields.One2many(
        string='Dados de Pagamento',
        comodel_name='account.invoice.payment',
        inverse_name='sale_id',
    )
    account_payment_line_ids = fields.One2many(
        string='Dados da cobrança',
        comodel_name='account.invoice.payment.line',
        inverse_name='sale_id',
    )

    def _fiscal_comment(self, cr, uid, order, context=None):
        fp_comment = []
        fc_comment = []
        fc_ids = []

        fp_comment = super(SaleOrder, self)._fiscal_comment(
            cr, uid, order, context)

        for line in order.order_line:
            if line.product_id.fiscal_classification_id:
                fc = line.product_id.fiscal_classification_id
                if fc.inv_copy_note and fc.note:
                    if fc.id not in fc_ids:
                        fc_comment.append(fc.note)
                        fc_ids.append(fc.id)

        return fp_comment + fc_comment

    @api.model
    def _make_invoice(self, order, lines):
        context = dict(self.env.context)
        company = self.env['res.company'].browse(
            self.env.user.company_id.id)
        context.update(
            {'fiscal_document_code': company.product_invoice_id.code})
        inv_id = super(SaleOrder,
                     self.with_context(context))._make_invoice(order,
                                                               lines)
        # TODO: Verificar o que deve ser feito com multiplas faturas para uma série de pagamentos
        # Devemos mesclar as parcelas? E se o faturamento não for 100%?
        # Mantemos a proporção / condição e refazemos as parcelas?
        order.account_payment_ids.write({'invoice_id': inv_id})
        return inv_id

    @api.multi
    def onchange_partner_id(self, part):
        result = super(SaleOrder, self).onchange_partner_id(part)
        # Sobrescreve o compartamento padrão do core de aplicar a forma de pagamento
        # verificar metodo: onchange_fiscal_payment_term
        if result.get('value'):
            result['value'].pop('payment_term', None)
        return result

    @api.onchange('fiscal_category_id', 'fiscal_position_id')
    def onchange_fiscal_payment_term(self):
        """ Quando a posição fiscal for preenchida temos os dados da categoria e do partner
        e então podemos tomar decidir qual o payment_term adequado
        :return:
        """
        partner_id = self.partner_invoice_id or self.partner_id

        payment_term = self.env['account.payment.term']
        # Busca do partner
        if partner_id and partner_id.property_payment_term:
            payment_term = partner_id.property_payment_term
        # Sobrecreve a opção do parceiro caso a categoria fiscal tenha uma opção definida

        if self.fiscal_category_id and self.fiscal_category_id.account_payment_term_id:
            payment_term = self.fiscal_category_id.account_payment_term_id
        self.payment_term = payment_term

    @api.onchange('payment_term', 'amount_total', 'date_order')
    def onchange_default_payment_term(self):
        """ Preenche a forma de pagamento padrão mantendo compatibilidade com o campo do core
        :return:
        """
        if (self.payment_term and self.amount_total and
                self.date_order and not self.account_payment_ids):
            payment_id = self.account_payment_ids.new()
            payment_id.payment_term_id = self.payment_term
            payment_id.amount = self.amount_total
            payment_id.date = self.date_order[:10]
            payment_id.onchange_payment_term_id()
            self.account_payment_ids |= payment_id


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.one
    @api.depends('price_unit', 'tax_id', 'discount', 'product_uom_qty')
    def _amount_line(self):
        price = self._calc_line_base_price()
        qty = self._calc_line_quantity()
        taxes = self.tax_id.compute_all(
            price,
            qty,
            product=self.product_id,
            partner=self.order_id.partner_invoice_id,
            fiscal_position=self.fiscal_position,
            insurance_value=self.insurance_value,
            freight_value=self.freight_value,
            other_costs_value=self.other_costs_value)

        self.price_subtotal = (self.order_id.pricelist_id
                               .currency_id.round(taxes['total']))
        self.price_gross = self._calc_price_gross(qty)
        self.discount_value = self.order_id.pricelist_id.currency_id.round(
            self.price_gross - (price * qty))

    insurance_value = fields.Float('Insurance',
                                   default=0.0,
                                   digits=dp.get_precision('Account'))
    other_costs_value = fields.Float('Other costs',
                                     default=0.0,
                                     digits=dp.get_precision('Account'))
    freight_value = fields.Float('Freight',
                                 default=0.0,
                                 digits=dp.get_precision('Account'))
    discount_value = fields.Float(compute='_amount_line',
                                  string='Vlr. Desc. (-)',
                                  digits=dp.get_precision('Sale Price'))
    price_gross = fields.Float(compute='_amount_line',
                               string='Vlr. Bruto',
                               digits=dp.get_precision('Sale Price'))
    price_subtotal = fields.Float(compute='_amount_line',
                                  string='Subtotal',
                                  digits=dp.get_precision('Sale Price'))
    customer_order = fields.Char(
        string=u"Pedido do Cliente",
        size=15,
    )
    customer_order_line = fields.Char(
        string=u"Item do Pedido do Cliente",
        size=6,
    )

    @api.onchange("customer_order_line")
    def _check_customer_order_line(self):
        if (self.customer_order_line and
                not self.customer_order_line.isdigit()):
            raise ValidationError(
                _(u"Customer order line must be "
                  "a number with up to six digits")
            )

    def _prepare_order_line_invoice_line(self, cr, uid, line,
                                         account_id=False, context=None):
        result = super(SaleOrderLine, self)._prepare_order_line_invoice_line(
            cr, uid, line, account_id, context)

        result['insurance_value'] = line.insurance_value
        result['other_costs_value'] = line.other_costs_value
        result['freight_value'] = line.freight_value
        result['partner_order'] = line.customer_order
        result['partner_order_line'] = line.customer_order_line

        # FIXME
        # Necessário informar estes campos pois são related do
        # objeto account.invoice e quando o método create do
        # account.invoice.line é invocado os valores são None
        result['company_id'] = line.order_id.company_id.id
        result['partner_id'] = line.order_id.partner_id.id

        if line.product_id.fiscal_type == 'product':
            if line.fiscal_position:
                cfop = self.pool.get("account.fiscal.position").read(
                    cr, uid, [line.fiscal_position.id], ['cfop_id'],
                    context=context)
                if cfop[0]['cfop_id']:
                    result['cfop_id'] = cfop[0]['cfop_id'][0]
        return result
