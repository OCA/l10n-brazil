# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2021 - TODAY Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import SITUACAO_EDOC_EM_DIGITACAO

OPERATION_TO_INVOICE = {
    'purchase': 'out',
    'purchase_refund': 'in',
    'return_in': 'in',
    'sale': 'out',
    'sale_refund': 'in',
    'return_out': 'out',
    'other': 'out',
}


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    invoice_ids = fields.One2many(
        comodel_name="account.invoice",
        inverse_name="fiscal_document_id",
        string="Invoices",
    )

    def _prepare_invoice_line_vals(self, line_vals, type, fpos):
        for line in self.line_ids:
            invoice_line_id = self.env['account.invoice.line']
            vals = self.env['account.invoice.line']._convert_to_write(
                line.read(invoice_line_id._fields.keys())[0]
            )
            vals['fiscal_document_line_id'] = vals.pop('id')
            vals['account_id'] = invoice_line_id.get_invoice_line_account(
                type=type,
                product=line.product_id,
                fpos=self.env['account.fiscal.position'].browse(fpos),
                company=line.company_id,
            ).id
            line_vals.append((0, 0, vals))

    def action_generate_invoice(self):
        invoice_id = self.env['account.invoice']
        for record in self:
            if not record.fiscal_operation_id:
                raise UserError(
                    _('Please fill the fiscal operation to continue!')
                )
            type = OPERATION_TO_INVOICE[record.fiscal_operation_id.fiscal_type]
            fpos = self.env['account.fiscal.position'].get_fiscal_position(
                record.partner_id.id,
                delivery_id=record.partner_shipping_id.id,
            )
            vals = invoice_id._convert_to_write(
                record.read(
                    record._fields.keys()
                )[0]
            )
            vals.pop('state')
            vals['fiscal_document_id'] = vals.pop('id')
            line_vals = []
            vals['invoice_line_ids'] = line_vals
            self._prepare_invoice_line_vals(line_vals, type, fpos)
            invoice_id = invoice_id.create(vals)

    def unlink(self):
        non_draft_documents = self.filtered(
            lambda d: d.state != SITUACAO_EDOC_EM_DIGITACAO
        )

        if non_draft_documents:
            UserError(
                _("You cannot delete a fiscal document " "which is not draft state.")
            )
        return super().unlink()
