# Copyright (C) 2009  Renato Lima - Akretion
# Copyright (C) 2012  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from lxml import etree
from functools import partial

from odoo import api, fields, models
from odoo.tools import float_is_zero
from odoo.tools.misc import formatLang


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
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
    )

    comment_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.comment',
        relation='sale_order_comment_rel',
        column1='sale_id',
        column2='comment_id',
        string='Comments',
    )

    @api.multi
    def _get_amount_lines(self):
        """Get object lines instaces used to compute fields"""
        return self.mapped('order_line')

    @api.depends('order_line')
    def _compute_amount(self):
        super()._compute_amount()

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """Compute the total amounts of the SO."""
        for order in self:
            order._compute_amount()

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
                if self.env.user.has_group(
                        'l10n_br_sale.group_discount_per_value'):
                    line.discount_value = (
                        (line.product_uom_qty * line.price_unit)
                        * (order.discount_rate / 100)
                    )
                    line._onchange_discount_value()
                else:
                    line.discount = order.discount_rate
                    line._onchange_discount_percent()

    @api.onchange('fiscal_operation_id')
    def _onchange_fiscal_operation_id(self):
        super()._onchange_fiscal_operation_id()
        self.fiscal_position_id = self.fiscal_operation_id.fiscal_position_id

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

                if inv_line.display_type:
                    continue

                fiscal_document_type = \
                    inv_line.fiscal_operation_line_id.get_document_type(
                        inv_line.invoice_id.company_id)

                if fiscal_document_type.id not in document_type_list:
                    document_type_list.append(fiscal_document_type.id)

            # Check if there more than one Document Type
            if ((fiscal_document_type.id !=
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

    # TODO open by default Invoice view with Fiscal Details Button
    # You can add a group to select default view Fiscal Invoice or
    # Account invoice.
    # @api.multi
    # def action_view_invoice(self):
    #     action = super().action_view_invoice()
    #     invoices = self.mapped('invoice_ids')
    #     if any(invoices.filtered(lambda i: i.document_type_id)):
    #         action = self.env.ref(
    #             'l10n_br_account.fiscal_invoice_out_action').read()[0]
    #         if len(invoices) > 1:
    #             action['domain'] = [('id', 'in', invoices.ids)]
    #         elif len(invoices) == 1:
    #             form_view = [
    #                 (self.env.ref(
    #                     'l10n_br_account.fiscal_invoice_form').id, 'form')
    #             ]
    #             if 'views' in action:
    #                 action['views'] = form_view + [
    #                     (state, view) for state, view in action['views']
    #                     if view != 'form']
    #             else:
    #                 action['views'] = form_view
    #             action['res_id'] = invoices.ids[0]
    #         else:
    #             action = {'type': 'ir.actions.act_window_close'}
    #     return action

    def _amount_by_group(self):
        for order in self:
            currency = order.currency_id or order.company_id.currency_id
            fmt = partial(
                formatLang,
                self.with_context(lang=order.partner_id.lang).env,
                currency_obj=currency
            )
            res = {}
            for line in order.order_line:
                taxes = line._compute_taxes(line.fiscal_tax_ids)['taxes']
                for tax in line.fiscal_tax_ids:
                    computed_tax = taxes.get(tax.tax_domain)
                    pr = order.currency_id.rounding
                    if computed_tax and not float_is_zero(
                            computed_tax.get('tax_value', 0.0), precision_rounding=pr):
                        group = tax.tax_group_id
                        res.setdefault(group, {'amount': 0.0, 'base': 0.0})
                        res[group]['amount'] += computed_tax.get('tax_value', 0.0)
                        res[group]['base'] += computed_tax.get('base', 0.0)
            res = sorted(res.items(), key=lambda l: l[0].sequence)
            order.amount_by_group = [(
                l[0].name, l[1]['amount'], l[1]['base'],
                fmt(l[1]['amount']), fmt(l[1]['base']),
                len(res),
            ) for l in res]
