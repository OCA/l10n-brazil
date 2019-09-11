# -*- coding: utf-8 -*-
# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import ast

from odoo import models, fields, api, _
from odoo.exceptions import Warning as UserError


class StockInvoiceOnshipping(models.TransientModel):
    _inherit = 'stock.invoice.onshipping'

    fiscal_category_journal = fields.Boolean(
        u'Diário da Categoria Fiscal', default=True)

    @api.multi
    def open_invoice(self):
        context = dict(self.env.context)
        for wizard in self:
            fiscal_document_code = (wizard.journal_id.company_id.
                                    product_invoice_id.code)
            context.update(
                {'fiscal_document_code': fiscal_document_code})
        result = super(StockInvoiceOnshipping,
                       self.with_context(context)).open_invoice()
        if result.get('context'):
            super_context = ast.literal_eval(result.get('context'))
            super_context.update(context)
            result['context'] = str(super_context)
        return result

    @api.multi
    def _build_invoice_values_from_pickings(self, pickings):

        result = {}
        picking = fields.first(pickings)
        journal_id = picking.fiscal_category_id.property_journal
        fiscal_document_code = picking.company_id.product_invoice_id.code
        context = dict(self.env.context)
        context.update(
            {'fiscal_document_code': fiscal_document_code})
        if not journal_id:
            raise UserError(
                _('Invalid Journal! There is not journal defined'
                  ' for this company: %s in fiscal operation: %s !') %
                (picking.company_id.name,
                 picking.fiscal_category_id.name))

        comment = ''
        if picking.fiscal_position_id.inv_copy_note:
            comment += picking.fiscal_position_id.note or ''
        if picking.note:
            comment += ' - ' + picking.note

        result['partner_shipping_id'] = picking.partner_id.id
        result['comment'] = comment
        result['fiscal_category_id'] = picking.fiscal_category_id.id
        result['fiscal_position_id'] = picking.fiscal_position_id.id
        result['fiscal_document_id'] = picking.company_id.product_invoice_id.id

        if picking.fiscal_category_id.journal_type in ('sale_refund',
                                                       'purchase_refund'):
            result['nfe_purpose'] = '4'
        values = super(StockInvoiceOnshipping, self
                       )._build_invoice_values_from_pickings(pickings)
        values.update(result)
        return values

    @api.multi
    def _get_invoice_line_values(self, moves, invoice):
        """
        Create invoice line values from given moves
        :param moves: stock.move
        :param invoice: account.invoice
        :return: dict
        """
        values = super(StockInvoiceOnshipping, self
                       )._get_invoice_line_values(
            moves, invoice)
        move = fields.first(moves)

        fiscal_position_id = move.fiscal_position_id or \
            move.picking_id.fiscal_position_id
        fiscal_category_id = move.fiscal_category_id or \
            move.picking_id.fiscal_category_id

        values['cfop_id'] = fiscal_position_id.cfop_id.id
        values['fiscal_category_id'] = fiscal_category_id.id
        values['fiscal_position_id'] = fiscal_position_id.id

        # TODO este código é um fix pq no core nao se copia os impostos
        ctx = dict(self.env.context)
        ctx['fiscal_type'] = move.product_id.fiscal_type
        ctx['partner_id'] = invoice.partner_id.id

        # Required to compute_all in account.invoice.line
        values['partner_id'] = invoice.partner_id.id

        ctx['product_id'] = move.product_id.id

        inv_type = invoice.type
        if inv_type in ('out_invoice', 'in_refund'):
            ctx['type_tax_use'] = 'sale'
            taxes = move.product_id.taxes_id
        else:
            ctx['type_tax_use'] = 'purchase'
            taxes = move.product_id.supplier_taxes_id

        if fiscal_position_id:
            taxes = fiscal_position_id.with_context(ctx).map_tax(
                taxes, move.product_id, move.partner_id)
        values['invoice_line_tax_ids'] = [[6, 0, taxes.ids]]

        if fiscal_position_id:
            account_id = values.get('account_id')
            account_id = fiscal_position_id.map_account(account_id)

        return values

    @api.multi
    def action_generate(self):
        """
        Launch the invoice generation
        :return:
        """
        self.ensure_one()
        invoices = self._action_generate_invoices()
        if not invoices:
            raise UserError(_('No invoice created!'))
        action = self.env.ref(
            'l10n_br_account_product.action_invoice_tree1_view1')
        action_dict = action.with_context(
            dict(fiscal_document_code='55')).read()[0]
        if action_dict:
            action_dict.update({
                'domain': [('id', 'in', invoices.ids)],
            })
            if len(invoices) == 1:
                action_dict.update({
                    'res_id': invoices.id,
                })
        return action_dict

    @api.multi
    def _action_generate_invoices(self):
        """
        Action to generate invoices based on pickings
        :return: account.invoice recordset
        """
        pickings = self._load_pickings()
        company = pickings.mapped("company_id")
        if company and company != self.env.user.company_id:
            raise UserError(_("All pickings are not related to your company!"))
        pick_list = self._group_pickings(pickings)
        invoices = self.env['account.invoice'].browse()
        for pickings in pick_list:
            invoice_values = self._build_invoice_values_from_pickings(pickings)
            invoice = self.env[
                'account.invoice'].with_context(dict(
                    fiscal_document_code=pickings.
                    company_id.product_invoice_id.code)
            ).create(invoice_values)
            moves = pickings.mapped("move_lines")
            moves_list = self._group_moves(moves)
            lines = []
            for moves in moves_list:
                line_values = self._get_invoice_line_values(moves, invoice)
                if line_values:
                    lines.append(line_values)
            if lines:
                invoice.write({
                    'invoice_line_ids': [(0, False, l) for l in lines],
                })
            invoice._onchange_invoice_line_ids()
            invoices |= invoice
        # Update the state on pickings related to new invoices only
        self._update_picking_invoice_status(invoices.mapped("picking_ids"))
        return invoices
