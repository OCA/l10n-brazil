# Copyright (C) 2009  Renato Lima - Akretion
# Copyright (C) 2012  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from lxml import etree

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = [_name, 'l10n_br_fiscal.document.mixin']

    @api.model
    def _default_fiscal_operation(self):
        return self.env.user.company_id.sale_fiscal_operation_id

    @api.model
    def _default_copy_note(self):
        return self.env.user.company_id.copy_note

    @api.model
    def _fiscal_operation_domain(self):
        domain = [('state', '=', 'approved')]
        return domain

    fiscal_operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_fiscal_operation,
        domain=lambda self: self._fiscal_operation_domain(),
    )

    ind_pres = fields.Selection(
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    copy_note = fields.Boolean(
        string='Copiar Observação no documentos fiscal',
        default=_default_copy_note,
    )

    cnpj_cpf = fields.Char(
        string='CNPJ/CPF',
        related='partner_id.cnpj_cpf',
    )

    legal_name = fields.Char(
        string='Legal Name',
        related='partner_id.legal_name',
    )

    ie = fields.Char(
        string='State Tax Number/RG',
        related='partner_id.inscr_est',
    )

    discount_rate = fields.Float(
        string='Discount',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    amount_gross = fields.Monetary(
        compute='_amount_all',
        string='Amount Gross',
        store=True,
        readonly=True,
        help="Amount without discount.",
    )

    amount_discount = fields.Monetary(
        compute='_amount_all',
        store=True,
        string='Discount (-)',
        readonly=True,
        help="The discount amount.",
    )

    amount_freight = fields.Float(
        compute='_amount_all',
        store=True,
        string='Freight',
        readonly=True,
        default=0.00,
        digits=dp.get_precision('Account'),
        states={'draft': [('readonly', False)]},
    )

    amount_insurance = fields.Float(
        compute='_amount_all',
        store=True,
        string='Insurance',
        readonly=True,
        default=0.00,
        digits=dp.get_precision('Account'),
    )

    amount_costs = fields.Float(
        compute='_amount_all',
        store=True,
        string='Other Costs',
        readonly=True,
        default=0.00,
        digits=dp.get_precision('Account'),
    )

    fiscal_document_count = fields.Integer(
        string='Fiscal Document Count',
        related='invoice_count',
        readonly=True,
    )

    comment_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.comment',
        relation='sale_order_comment_rel',
        column1='sale_id',
        column2='comment_id',
        string='Comments',
    )

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """Compute the total amounts of the SO."""
        for order in self:
            order.amount_gross = sum(
                line.price_gross for line in order.order_line)

            order.amount_discount = sum(
                line.discount_value for line in order.order_line)

            order.amount_untaxed = sum(
                line.price_subtotal for line in order.order_line)

            order.amount_tax = sum(
                line.price_tax for line in order.order_line)

            order.amount_total = sum(
                line.price_total for line in order.order_line)

            order.amount_freight = sum(
                line.freight_value for line in order.order_line)

            order.amount_costs = sum(
                line.other_costs_value for line in order.order_line)

            order.amount_insurance = sum(
                line.insurance_value for line in order.order_line)

    @api.model
    def fields_view_get(self, view_id=None, view_type="form",
                        toolbar=False, submenu=False):

        order_view = super().fields_view_get(
            view_id, view_type, toolbar, submenu
        )

        if view_type == 'form':
            sub_form_view = order_view.get(
                'fields', {}).get('order_line', {}).get(
                'views', {}).get('form', {}).get('arch', {})

            view = self.env['ir.ui.view']

            sub_form_node = etree.fromstring(
                self.env['sale.order.line'].fiscal_form_view(sub_form_view))

            sub_arch, sub_fields = view.postprocess_and_fields(
                'sale.order.line', sub_form_node, None)

            order_view['fields']['order_line']['views']['form'][
                'fields'] = sub_fields

            order_view['fields']['order_line']['views']['form'][
                'arch'] = sub_arch

        return order_view

    @api.onchange('discount_rate')
    def onchange_discount_rate(self):
        for order in self:
            for line in order.order_line:
                line.discount = order.discount_rate
                line._onchange_discount_percent()

    @api.onchange('fiscal_operation_id')
    def _onchange_fiscal_operation_id(self):
        super()._onchange_fiscal_operation_id()
        self.fiscal_position_id = self.fiscal_operation_id.fiscal_position_id

    @api.multi
    def action_view_document(self):
        invoices = self.mapped('invoice_ids')
        action = self.env.ref('l10n_br_fiscal.document_out_action').read()[0]
        if len(invoices) > 1:
            action['domain'] = [
                ('id', 'in', invoices.mapped('fiscal_document_id').ids),
            ]
        elif len(invoices) == 1:
            form_view = [
                (self.env.ref('l10n_br_fiscal.document_form').id, 'form'),
            ]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view
                                               in action['views'] if
                                               view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.fiscal_document_id.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def _prepare_invoice(self):
        self.ensure_one()
        result = super()._prepare_invoice()
        result.update(self._prepare_br_fiscal_dict())

        document_type_id = self._context.get('document_type_id')

        if document_type_id:
            document_type = self.env['l10n_br_fiscal.document.type'].browse(
                document_type_id)
        else:
            document_type = self.company_id.document_type_id
            document_type_id = self.company_id.document_type_id.id

        if document_type:
            result['document_type_id'] = document_type_id
            document_serie = document_type.get_document_serie(
                self.company_id, self.fiscal_operation_id)
            if document_serie:
                result['document_serie_id'] = document_serie.id

        if self.fiscal_operation_id:
            if self.fiscal_operation_id.journal_id:
                result['journal_id'] = self.fiscal_operation_id.journal_id.id

        return result

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):

        inv_ids = super().action_invoice_create(grouped=grouped, final=final)

        # In brazilian localization we need to overwrite this method
        # because when there are a sale order line with different Document
        # Fiscal Type the method should be create invoices separated.
        document_type_list = []

        for invoice_id in inv_ids:
            invoice_created_by_super = self.env[
                'account.invoice'].browse(invoice_id)

            # Identify how many Document Types exist
            for inv_line in invoice_created_by_super.invoice_line_ids:

                fiscal_document_type = \
                    inv_line.fiscal_operation_line_id.get_document_type(
                        inv_line.invoice_id.company_id)

                if fiscal_document_type.id not in document_type_list:
                    document_type_list.append(fiscal_document_type.id)

            # Check if there more than one Document Type
            if ((fiscal_document_type !=
                    invoice_created_by_super.document_type_id.id) or
                    (len(document_type_list) > 1)):

                # Remove the First Document Type,
                # already has Invoice created
                invoice_created_by_super.document_type_id =\
                    document_type_list.pop(0)

                for document_type in document_type_list:
                    document_type = self.env[
                        'l10n_br_fiscal.document.type'].browse(document_type)

                    inv_obj = self.env['account.invoice']
                    invoices = {}
                    references = {}
                    invoices_origin = {}
                    invoices_name = {}

                    for order in self:
                        group_key = order.id if grouped else (
                            order.partner_invoice_id.id, order.currency_id.id)

                        if group_key not in invoices:
                            inv_data = order.with_context(
                                document_type_id=document_type.id
                            )._prepare_invoice()
                            invoice = inv_obj.create(inv_data)
                            references[invoice] = order
                            invoices[group_key] = invoice
                            invoices_origin[group_key] = [invoice.origin]
                            invoices_name[group_key] = [invoice.name]
                            inv_ids.append(invoice.id)
                        elif group_key in invoices:
                            if order.name not in invoices_origin[group_key]:
                                invoices_origin[group_key].append(order.name)
                            if (order.client_order_ref and
                               order.client_order_ref not in
                               invoices_name[group_key]):
                                invoices_name[group_key].append(
                                    order.client_order_ref)

                    # Update Invoice Line
                    for inv_line in invoice_created_by_super.invoice_line_ids:
                        fiscal_document_type = \
                            inv_line.fiscal_operation_line_id.get_document_type(
                                inv_line.invoice_id.company_id)
                        if fiscal_document_type.id == document_type.id:
                            inv_line.invoice_id = invoice.id

        return inv_ids
