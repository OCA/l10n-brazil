# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import ast

from odoo import models, fields, api, _
from odoo.exceptions import Warning as UserError


class StockInvoiceOnshipping(models.TransientModel):
    _inherit = 'stock.invoice.onshipping'

    fiscal_operation_journal = fields.Boolean(
        string='Account Jornal from Fiscal Operation',
        default=True,
    )

    group = fields.Selection(
        selection_add=[
            ('fiscal_operation', 'Fiscal Operation')],
    )

    @api.multi
    def _get_journal(self):
        """
        Get the journal depending on the journal_type
        :return: account.journal recordset
        """
        self.ensure_one()
        journal = self.env['account.journal']
        if self.fiscal_operation_journal:
            pickings = self._load_pickings()
            picking = fields.first(pickings)
            journal = picking.fiscal_operation_id.journal_id
            if not journal:
                raise UserError(
                    _('Invalid Journal! There is not journal defined'
                      ' for this company: %s in fiscal operation: %s !') %
                    (picking.company_id.name,
                     picking.fiscal_operation_id.name))
        else:
            journal = super(StockInvoiceOnshipping, self)._get_journal()
        return journal

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
        picking = fields.first(pickings)
        invoice, values = super()._build_invoice_values_from_pickings(pickings)
        fiscal_values = picking._prepare_br_fiscal_dict()
        values.update(fiscal_values)
        return invoice, values

    @api.multi
    def _get_invoice_line_values(self, moves, invoice_values, invoice):
        """
        Create invoice line values from given moves
        :param moves: stock.move
        :param invoice: account.invoice
        :return: dict
        """
        values = super()._get_invoice_line_values(
            moves, invoice_values, invoice)

        move = fields.first(moves)
        fiscal_values = move._prepare_br_fiscal_dict()
        values.update(fiscal_values)
        return values
