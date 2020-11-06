# Copyright (C) 2014  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = [_name, 'l10n_br_fiscal.document.mixin']

    @api.model
    def _default_fiscal_operation(self):
        company = self.env.user.company_id
        fiscal_operation = self.env.user.company_id.stock_fiscal_operation_id
        picking_type_id = self.env.context.get('default_picking_type_id')
        if picking_type_id:
            picking_type = self.env['stock.picking.type'].browse(
                picking_type_id)
            fiscal_operation = picking_type.fiscal_operation_id or (
                company.stock_in_fiscal_operation_id
                if picking_type.code == 'incoming'
                else company.stock_out_fiscal_operation_id
            )
        return fiscal_operation

    @api.model
    def _fiscal_operation_domain(self):
        # TODO Check in context to define in or out move default.
        domain = [('state', '=', 'approved')]
        return domain

    fiscal_operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=_default_fiscal_operation,
        domain=lambda self: self._fiscal_operation_domain(),
    )

    comment_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.comment',
        relation='stock_picking_comment_rel',
        column1='picking_id',
        column2='comment_id',
        string='Comments',
    )

    @api.onchange('fiscal_operation_id')
    def _onchange_fiscal_operation_id(self):
        super()._onchange_fiscal_operation_id()
        if self.fiscal_operation_id:
            self.invoice_state = self.fiscal_operation_id.invoice_state

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
