# -*- coding: utf-8 -*-
# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel
# Copyright (C) 2012  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api, _
from odoo.exceptions import except_orm
from odoo.addons import decimal_precision as dp


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.one
    @api.depends('order_line.price_unit', 'order_line.product_qty',
                 'order_line.taxes_id')
    def _compute_amount(self):
        amount_untaxed = 0.0
        amount_tax = 0.0

        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                if (order.company_id.tax_calculation_rounding_method
                        == 'round_globally'):
                    taxes = line.taxes_id.compute_all(
                        line.price_unit, line.order_id.currency_id,
                        line.product_qty, product=line.product_id,
                        partner=line.order_id.partner_id)
                    amount_tax += sum(
                        t.get('amount', 0.0) for t in taxes.get('taxes', []))
                else:
                    amount_tax += line.price_tax
            order.update({
                'amount_untaxed': order.currency_id.round(amount_untaxed),
                'amount_tax': order.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })

        self.amount_untaxed = self.currency_id.round(
            amount_untaxed)
        self.amount_tax = self.currency_id.round(amount_tax)
        self.amount_total = self.currency_id.round(
            amount_untaxed + amount_tax)

    @api.model
    @api.returns('l10n_br_account.fiscal_category')
    def _default_fiscal_category(self):
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        return company.purchase_fiscal_category_id

    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Categoria Fiscal',
        default=_default_fiscal_category,
        domain="""[('type', '=', 'input'), ('state', '=', 'approved'),
            ('journal_type', '=', 'purchase')]""")
    amount_untaxed = fields.Monetary(
        compute='_compute_amount', digits=dp.get_precision('Purchase Price'),
        string='Untaxed Amount', store=True, help="The amount without tax")
    amount_tax = fields.Monetary(
        compute='_compute_amount', digits=dp.get_precision('Purchase Price'),
        string='Taxes', store=True, help="The tax amount")
    amount_total = fields.Monetary(
        compute='_compute_amount', digits=dp.get_precision('Purchase Price'),
        string='Total', store=True, help="The total amount")

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
        """Método para chamar a definição de regras fiscais"""
        ctx = dict(self._context)
        if not kwargs.get('fiscal_category_id'):
            kwargs['fiscal_category_id'] = ctx.get('fiscal_category_id')

        ctx.update({
            'use_domain': ('use_purchase', '=', True),
            'fiscal_category_id': ctx.get('fiscal_category_id')
        })
        return self.env[
            'account.fiscal.position.rule'].with_context(
                ctx).apply_fiscal_mapping(**kwargs)

    @api.onchange('fiscal_category_id', 'fiscal_position_id')
    def onchange_fiscal(self):

        if self.partner_id and self.company_id:
            kwargs = {
                'company_id': self.company_id,
                'partner_id': self.partner_id,
                'partner_invoice_id': self.partner_id,
                'fiscal_category_id': self.fiscal_category_id,
                'partner_shipping_id': self.dest_address_id,
            }
            fiscal_position = self._fiscal_position_map(**kwargs)

            if fiscal_position:
                self.fiscal_position_id = fiscal_position.id

    @api.model
    def _prepare_picking(self):
        vals = super(PurchaseOrder, self)._prepare_picking()
        vals.update({
            'fiscal_category_id': (self.fiscal_category_id.id),
            'fiscal_position_id': self.fiscal_position_id.id,
        })
        return vals

    @api.model
    def _create_stock_moves(self, order, order_lines, picking_id=None):
        result = super(PurchaseOrder, self)._create_stock_moves(
            order, order_lines, picking_id)
        if picking_id:
            picking_values = {
                'fiscal_category_id': order.fiscal_category_id.id,
                'fiscal_position': order.fiscal_position.id,
            }
            picking = self.env['stock.picking'].browse(picking_id)
            picking.write(picking_values)
        return result


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Categoria Fiscal',
        domain="[('type', '=', 'input'), ('journal_type', '=', 'purchase')]")
    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', u'Posição Fiscal',
        domain="[('fiscal_category_id', '=', fiscal_category_id)]")

    @api.model
    def _fiscal_position_map(self, **kwargs):
        result = {'value': {}}
        context = dict(self.env.context)
        context.update({'use_domain': ('use_purchase', '=', True)})
        fp_rule_obj = self.env['account.fiscal.position.rule']

        partner_invoice = kwargs.get('partner_invoice_id')

        product_fc_id = fp_rule_obj.with_context(
            context).product_fiscal_category_map(
                kwargs.get('product_id'),
                kwargs.get('fiscal_category_id'),
                partner_invoice.state_id.id)

        if product_fc_id:
            kwargs['fiscal_category_id'] = product_fc_id

        result['value']['fiscal_category_id'] = kwargs.get(
            'fiscal_category_id')

        obj_fiscal_position = fp_rule_obj.with_context(
            context).apply_fiscal_mapping(**kwargs)
        obj_product = kwargs.get('product_id')

        if obj_product and obj_fiscal_position:
            result['value']['fiscal_position_id'] = obj_fiscal_position
            context.update({
                'fiscal_type': obj_product.fiscal_type,
                'type_tax_use': 'purchase', 'product_id': obj_product.id})
            taxes = obj_product.taxes_id
            tax_ids = obj_fiscal_position.with_context(context).map_tax(
                taxes, obj_product, partner_invoice)
            result['value']['taxes_id'] = tax_ids

        return result

    @api.multi
    @api.onchange('product_id')
    def onchange_product_id(self):
        """Método para implementar a inclusão dos campos categoria fiscal
        e posição fiscal de acordo com valores padrões e regras de posicões
        fiscais
        """
        result = super(PurchaseOrderLine, self).onchange_product_id()

        ctx = dict(self.env.context)
        company_id = ctx.get('company_id')
        parent_fiscal_category_id = ctx.get('parent_fiscal_category_id')

        if self.product_id and parent_fiscal_category_id and self.partner_id:
            kwargs = {
                'company_id': company_id,
                'product_id': self.product_id,
                'partner_id': self.partner_id,
                'partner_invoice_id': self.partner_id,
                'fiscal_category_id': parent_fiscal_category_id,
                'context': ctx,
            }
            fiscal_position = self._fiscal_position_map(**kwargs)
            if fiscal_position:
                result['fiscal_position_id'] = fiscal_position.id

            ctx.update({'fiscal_type': self.product_id.fiscal_type,
                        'type_tax_use': 'purchase'})

        return result

    @api.multi
    @api.onchange('fiscal_category_id', 'fiscal_position_id')
    def onchange_fiscal(self):
        for record in self:
            if record.order_id.company_id and record.order_id.partner_id \
                    and record.fiscal_category_id:
                kwargs = {
                    'company_id': record.order_id.company_id,
                    'partner_id': record.order_id.partner_id,
                    'partner_invoice_id': record.order_id.partner_id,
                    'product_id': record.product_id,
                    'fiscal_category_id': record.fiscal_category_id or
                    record.order_id.fiscal_category_id,
                    'context': record.env.context
                }
                result = record._fiscal_position_map(**kwargs)
                kwargs.update({
                    'fiscal_category_id': record.fiscal_category_id.id,
                    'fiscal_position_id': record.fiscal_position_id.id,
                    'taxes_id': [(6, 0, record.taxes_id.ids)],
                })
                record.update(result['value'])

    @api.multi
    def _prepare_stock_moves(self, picking):
        """
        Prepare the stock moves data for one order line.
         This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        vals = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        vals[0].update({
            'fiscal_category_id': self.fiscal_category_id.id,
            'fiscal_position_id': self.fiscal_position_id.id,
        })
        return vals
