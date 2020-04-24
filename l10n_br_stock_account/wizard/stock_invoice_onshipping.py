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
        journal_id = picking.operation_id.journal_id

        if not journal_id:
            raise UserError(
                _('Invalid Journal! There is not journal defined'
                  ' for this company: %s in fiscal operation: %s !') %
                (picking.company_id.name,
                 picking.operation_id.name))

        comment = ''
        # TODO - Comments
        # if picking.fiscal_position_id.inv_copy_note:
        #     comment += picking.fiscal_position_id.note or ''
        # if picking.note:
        #     comment += ' - ' + picking.note

        result['partner_shipping_id'] = picking.partner_id.id
        result['comment'] = comment

        # TODO - Should we identify when create fiscal document ?
        result['fiscal_document_id'] = False
        result['operation_id'] = picking.operation_id.id
        result['document_type_id'] = self._context.get('document_type_id')
        result['operation_type'] = picking.operation_id.operation_type

        if picking.operation_id.operation_type in (
                'sale_refund', 'purchase_refund'):
            result['nfe_purpose'] = '4'
        values = super(StockInvoiceOnshipping, self
                       )._build_invoice_values_from_pickings(pickings)
        values[1].update(result)
        return values

    @api.multi
    def _get_invoice_line_values(self, moves, invoice_values, invoice):
        """
        Create invoice line values from given moves
        :param moves: stock.move
        :param invoice: account.invoice
        :return: dict
        """
        values = super(StockInvoiceOnshipping, self
                       )._get_invoice_line_values(
            moves, invoice_values, invoice)
        move = fields.first(moves)

        values['cfop_id'] = move.cfop_id.id
        values['operation_id'] = move.operation_id.id or \
            move.picking_id.operation_id.id
        values['operation_line_id'] = move.operation_line_id.id
        values['partner_id'] = invoice.partner_id.id

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

        # Update the state on pickings related to new invoices only
        self._update_picking_invoice_status(invoices.mapped("picking_ids"))

        inv_type = self._get_invoice_type()
        # TODO - Are change the view to brazilian localization ?
        if inv_type in ["out_invoice", "out_refund"]:
            action = self.env.ref("account.action_invoice_tree1")
        else:
            action = self.env.ref("account.action_vendor_bill_template")

        action_dict = action.read()[0]

        if len(invoices) > 1:
            action_dict['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            if inv_type in ["out_invoice", "out_refund"]:
                form_view = [(self.env.ref('account.invoice_form').id, 'form')]
            else:
                form_view = [(self.env.ref(
                    'account.invoice_supplier_form').id, 'form')]
            if 'views' in action_dict:
                action_dict['views'] = form_view + [
                    (state,  view) for state, view in action[
                        'views'] if view != 'form']
            else:
                action_dict['views'] = form_view
            action_dict['res_id'] = invoices.ids[0]

        return action_dict

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
            moves = pickings.mapped("move_lines")
            grouped_moves_list = self._group_moves(moves)
            parts = self.ungroup_moves(grouped_moves_list)

            # The field document_type_id are in a function of operation_line_id
            # but the method used to create lines need to the invoice was created
            # to called, by this reason we need to get this information before the
            # FOR code used to create the invoice lines
            # TODO - Are better way to make it ?
            move = fields.first(pickings.move_lines)
            document_type_id = move.operation_line_id.get_document_type(
                move.picking_id.company_id).id

            for moves_list in parts:
                invoice, invoice_values = self.with_context(
                    document_type_id=document_type_id
                )._build_invoice_values_from_pickings(pickings)
                lines = [(5, 0, {})]
                for moves in moves_list:
                    line_values = self._get_invoice_line_values(
                        moves, invoice_values, invoice
                    )
                    if line_values:
                        lines.append((0, 0, line_values))
                if line_values:  # Only create the invoice if it have lines
                    invoice_values['invoice_line_ids'] = lines
                    invoice = self._create_invoice(invoice_values)
                    invoice._onchange_invoice_line_ids()
                    invoice.compute_taxes()
                    invoices |= invoice
        return invoices
