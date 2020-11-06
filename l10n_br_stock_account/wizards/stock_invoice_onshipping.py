# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import UserError


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
            journal = super()._get_journal()
        return journal

    @api.multi
    def _build_invoice_values_from_pickings(self, pickings):
        invoice, values = super()._build_invoice_values_from_pickings(pickings)
        pick = fields.first(pickings)
        fiscal_vals = pick._prepare_br_fiscal_dict()

        document_type_id = self._context.get('document_type_id')

        if document_type_id:
            document_type = self.env['l10n_br_fiscal.document.type'].browse(
                document_type_id)
        else:
            document_type = pick.company_id.document_type_id
            document_type_id = pick.company_id.document_type_id.id

        fiscal_vals['document_type_id'] = document_type_id
        document_serie = document_type.get_document_serie(
            pick.company_id, pick.fiscal_operation_id)
        if document_serie:
            fiscal_vals['document_serie_id'] = document_serie.id

        if pick.fiscal_operation_id and pick.fiscal_operation_id.journal_id:
            fiscal_vals['journal_id'] = pick.fiscal_operation_id.journal_id.id

        values.update(fiscal_vals)
        return invoice, values

    @api.multi
    def _get_invoice_line_values(self, moves, invoice_values, invoice):
        """
        Create invoice line values from given moves
        :param moves: stock.move
        :param invoice: account.invoice
        :return: dict
        """

        move = fields.first(moves)
        values = move._prepare_br_fiscal_dict()
        values.update(
            {
                key: value for key, value in super()._get_invoice_line_values(
                    moves, invoice_values, invoice
                ).items() if value
            }
        )
        values['invoice_line_tax_ids'] = [
            (6, 0, self.env['l10n_br_fiscal.tax'].browse(
                values['fiscal_tax_ids'][0][2]
            ).account_taxes().ids)
        ]
        return values
