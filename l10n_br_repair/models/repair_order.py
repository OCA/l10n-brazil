# Copyright 2020 - TODAY, Marcel Savegnago - Escodoo - https://www.escodoo.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression


class RepairOrder(models.Model):
    _name = 'repair.order'
    _inherit = [_name, 'l10n_br_fiscal.document.mixin']

    @api.model
    def _default_fiscal_operation(self):
        return self.env.user.company_id.repair_fiscal_operation_id

    @api.model
    def _default_copy_note(self):
        return self.env.user.company_id.copy_repair_quotation_notes

    @api.model
    def _fiscal_operation_domain(self):
        domain = [('state', '=', 'approved')]
        return domain

    # fiscal_position_id = fields.Many2one(
    #     comodel_name='account.fiscal.position',
    #     oldname='fiscal_position',
    #     string='Fiscal Position'
    # )

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

    copy_repair_quotation_notes = fields.Boolean(
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

    fiscal_document_count = fields.Integer(
        string='Fiscal Document Count',
        related='invoice_count',
        readonly=True,
    )

    comment_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.comment',
        relation='repair_order_comment_rel',
        column1='repair_id',
        column2='comment_id',
        string='Comments',
    )

    currency_id = fields.Many2one(
        string='Currency ID',
        related='partner_id.currency_id')

    invoice_count = fields.Integer(string='Invoice Count',
                                   compute='_get_invoiced', readonly=True)

    invoice_ids = fields.Many2many("account.invoice", string='Invoices',
                                   compute="_get_invoiced", readonly=True,
                                   copy=False)

    client_order_ref = fields.Char(string='Customer Reference', copy=False)

    @api.multi
    def _get_amount_lines(self):
        """Get object lines instaces used to compute fields"""
        lines = []
        lines += [l for l in self.mapped('operations')]
        lines += [l for l in self.mapped('fees_lines')]
        return lines

    @api.depends('operations.price_total', 'fees_lines.price_total')
    def _compute_amount(self):
        super()._compute_amount()

    @api.depends('operations.price_total', 'fees_lines.price_total')
    def _amount_all(self):
        """Compute the total amounts of the RO."""
        self._compute_amount()

    @api.depends('state', 'operations.invoice_line_id', 'fees_lines.invoice_line_id')
    def _get_invoiced(self):
        """
        Compute the invoice status of a SO. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is
          nothing to invoice. This is also the default value if the conditions of no
          other status is met.
        - to invoice: if any SO line is 'to invoice', the whole SO is 'to invoice'
        - invoiced: if all SO lines are invoiced, the SO is invoiced.
        - upselling: if all SO lines are invoiced or upselling, the status is
          upselling.

        The invoice_ids are obtained thanks to the invoice lines of the SO lines, and
        we also search for possible refunds created directly from existing
        invoices. This is necessary since such a refund is not directly linked to
        the SO.
        """
        # Ignore the status of the deposit product
        # deposit_product_id = self.env['sale.advance.payment.inv']\
        #     ._default_product_id()

        for order in self:
            invoice_ids = \
                order.operations.mapped('invoice_line_id')\
                .mapped('invoice_id')\
                .filtered(lambda r: r.type in ['out_invoice', 'out_refund']) + \
                order.fees_lines.mapped('invoice_line_id')\
                .mapped('invoice_id')\
                .filtered(lambda r: r.type in ['out_invoice', 'out_refund'])
            # Search for invoices which have been
            # 'cancelled' (filter_refund = 'modify' in account.invoice.refund')
            # use like as origin may contains multiple
            # references (e.g. 'SO01, SO02')
            refunds = invoice_ids.search([
                ('origin', 'like', order.name),
                ('company_id', '=', order.company_id.id),
                ('type', 'in', ('out_invoice', 'out_refund'))
            ])

            invoice_ids |= refunds.filtered(lambda r: order.name in [
                origin.strip() for origin in r.origin.split(',')])

            # Search for refunds as well
            domain_inv = expression.OR([
                [
                    '&',
                    ('origin', '=', inv.number),
                    ('journal_id', '=', inv.journal_id.id)
                ]
                for inv in invoice_ids if inv.number
            ])

            if domain_inv:
                refund_ids = self.env['account.invoice'].search(expression.AND([
                    ['&', ('type', '=', 'out_refund'), ('origin', '!=', False)],
                    domain_inv
                ]))
            else:
                refund_ids = self.env['account.invoice'].browse()

            order.update({
                'invoice_count': len(set(invoice_ids.ids + refund_ids.ids)),
                'invoice_ids': invoice_ids.ids + refund_ids.ids,
            })

    @api.model
    def fields_view_get(self, view_id=None, view_type="form",
                        toolbar=False, submenu=False):

        order_view = super().fields_view_get(
            view_id, view_type, toolbar, submenu
        )

        if view_type == 'form':
            sub_form_view = order_view.get(
                'fields', {}).get('operations', {}).get(
                'views', {}).get('form', {}).get('arch', {})

            view = self.env['ir.ui.view']

            sub_form_node = etree.fromstring(
                self.env['repair.line'].fiscal_form_view(sub_form_view))

            sub_arch, sub_fields = view.postprocess_and_fields(
                'repair.line', sub_form_node, None)

            order_view['fields']['operations']['views']['form'][
                'fields'] = sub_fields

            order_view['fields']['operations']['views']['form'][
                'arch'] = sub_arch

        if view_type == 'form':
            sub_form_view = order_view.get(
                'fields', {}).get('fees_lines', {}).get(
                'views', {}).get('form', {}).get('arch', {})

            view = self.env['ir.ui.view']

            sub_form_node = etree.fromstring(
                self.env['repair.fee'].fiscal_form_view(sub_form_view))

            sub_arch, sub_fields = view.postprocess_and_fields(
                'repair.fee', sub_form_node, None)

            order_view['fields']['fees_lines']['views']['form'][
                'fields'] = sub_fields

            order_view['fields']['fees_lines']['views']['form'][
                'arch'] = sub_arch

        return order_view

    @api.onchange('discount_rate')
    def onchange_discount_rate(self):
        for order in self:
            for line in order.operations:
                line.discount = order.discount_rate
                line._onchange_discount_percent()
            for line in order.fees_lines:
                line.discount_value = order.discount_rate
                line._onchange_discount_percent()

    # @api.onchange('fiscal_operation_id')
    # def _onchange_fiscal_operation_id(self):
    #     super()._onchange_fiscal_operation_id()
    #     self.fiscal_position_id = self.fiscal_operation_id.fiscal_position_id

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
    def action_view_invoice(self):
        invoices = self.mapped('invoice_ids')
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = \
                [(self.env.ref('account.invoice_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view
                                               in action['views'] if
                                               view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def _prepare_invoice(self):
        self.ensure_one()
        # self.update(self._prepare_br_fiscal_dict())
        company_id = self.company_id.id

        if not self.company_id.document_type_id:
            raise UserError(_(
                'Please define an default document type for this company.'))

        journal_id = (self.env['account.invoice'].with_context(
            company_id=company_id or self.env.user.company_id.id)
            .default_get(['journal_id'])['journal_id'])
        if not journal_id:
            raise UserError(_(
                'Please define an accounting sales journal for this company.'))

        vinvoice = self.env['account.invoice'].new({
            'partner_id': self.partner_invoice_id.id,
            'type': 'out_invoice'
        })

        # Get partner extra fields
        vinvoice._onchange_partner_id()
        invoice_vals = vinvoice._convert_to_write(vinvoice._cache)

        fp_id = \
            self.partner_id.property_account_position_id.id or \
            self.env['account.fiscal.position'].get_fiscal_position(
                self.partner_id.id, delivery_id=self.address_id.id)

        invoice_vals.update({
            'name': (self.client_order_ref or '')[:2000],
            'origin': self.name,
            'type': 'out_invoice',
            'account_id': self.partner_invoice_id.property_account_receivable_id.id,
            'journal_id': journal_id,
            'currency_id': self.pricelist_id.currency_id.id,
            'company_id': company_id,
            'comment': self.quotation_notes,
            'fiscal_position_id': fp_id,
        })

        invoice_vals.update(self._prepare_br_fiscal_dict())

        document_type_id = self._context.get('document_type_id')

        if document_type_id:
            document_type = self.env['l10n_br_fiscal.document.type'].browse(
                document_type_id)
        else:
            document_type = self.company_id.document_type_id
            document_type_id = self.company_id.document_type_id.id

        invoice_vals['document_type_id'] = document_type_id

        document_serie = document_type.get_document_serie(
            self.company_id, self.fiscal_operation_id)

        if document_serie:
            invoice_vals['document_serie_id'] = document_serie.id

        if self.fiscal_operation_id:
            if self.fiscal_operation_id.journal_id:
                invoice_vals['journal_id'] = self.fiscal_operation_id.journal_id.id

        # if self.fiscal_position_id:
        #     invoice_vals['fiscal_position_id'] = self.fiscal_position_id

        return invoice_vals

    @api.multi
    def action_invoice_create(self, group=False):
        """ Creates invoice(s) for repair order.
        @param group: It is set to true when group invoice is to be generated.
        @return: Invoice Ids.
        """
        res = dict.fromkeys(self.ids, False)
        invoices_group = {}
        InvoiceLine = self.env['account.invoice.line']
        Invoice = self.env['account.invoice']

        for repair in \
            self.filtered(lambda repair:
                          repair.state not in
                          ('draft', 'cancel') and not
                          repair.invoice_id):

            if not repair.partner_id.id and not repair.partner_invoice_id.id:
                raise UserError(_(
                    'You have to select an invoice address in the repair form.'))

            comment = repair.quotation_notes

            if repair.invoice_method != 'none':
                if group and repair.partner_invoice_id.id in invoices_group:
                    invoice = invoices_group[repair.partner_invoice_id.id]
                    invoice.write({
                        'name': invoice.name + ', ' + repair.name,
                        'origin': invoice.origin + ', ' + repair.name,
                        'comment': (comment and (invoice.comment and
                                                 invoice.comment + "\n" + comment or
                                                 comment)) or
                                   (invoice.comment and invoice.comment or ''),
                    })
                else:
                    if not repair.partner_id.property_account_receivable_id:
                        raise UserError(_(
                            'No account defined for partner "%s".'
                        ) % repair.partner_id.name)

                    inv_data = self._prepare_invoice()
                    invoice = Invoice.create(inv_data)
                    invoices_group[repair.partner_invoice_id.id] = invoice

                repair.write({'invoiced': True, 'invoice_id': invoice.id})

                for operation in repair.operations:
                    if operation.type == 'add':

                        inv_line_data = operation\
                            ._prepare_invoice_line(operation.product_uom_qty)

                        inv_line_data['invoice_id'] = invoice.id

                        invoice_line = InvoiceLine.create(inv_line_data)

                        operation.write({
                            'invoiced': True,
                            'invoice_line_id': invoice_line.id
                        })

                for fee in repair.fees_lines:
                    if not fee.product_id:
                        raise UserError(_('No product defined on fees.'))

                    inv_line_data = fee._prepare_invoice_line(fee.product_uom_qty)

                    inv_line_data['invoice_id'] = invoice.id

                    invoice_line = InvoiceLine.create(inv_line_data)

                    fee.write({'invoiced': True, 'invoice_line_id': invoice_line.id})

                invoice.compute_taxes()

                res[repair.id] = invoice.id

                document_type_list = []

                # for invoice_id in invoice_id:
                invoice_created_by_super = self.env[
                    'account.invoice'].browse(res[repair.id])

                # Identify how many Document Types exist
                for inv_line in invoice_created_by_super.invoice_line_ids:

                    fiscal_document_type = \
                        inv_line.fiscal_operation_line_id.get_document_type(
                            inv_line.invoice_id.company_id)

                    if fiscal_document_type.id not in document_type_list:
                        document_type_list.append(fiscal_document_type.id)

                # Check if there more than one Document Type
                if ((fiscal_document_type !=
                        invoice_created_by_super.document_type_id) or
                        (len(document_type_list) > 1)):
                    # Remove the First Document Type,
                    # already has Invoice created
                    invoice_created_by_super.document_type_id = \
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
                            group_key = order.id if group else (
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
                                # inv_ids.append(invoice.id)
                            elif group_key in invoices:

                                if order.name not in invoices_origin[group_key]:
                                    invoices_origin[group_key].append(order.name)

                                if (order.client_order_ref and order.client_order_ref
                                   not in invoices_name[group_key]):
                                    invoices_name[group_key]\
                                        .append(order.client_order_ref)

                        # Update Invoice Line
                        for inv_line in invoice_created_by_super.invoice_line_ids:
                            fiscal_document_type = \
                                inv_line.fiscal_operation_line_id.get_document_type(
                                    inv_line.invoice_id.company_id)
                            if fiscal_document_type.id == document_type.id:
                                inv_line.invoice_id = invoice.id
                                inv_line.document_id = invoice.fiscal_document_id

        return res
