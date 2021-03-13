# Copyright (C) 2016-TODAY Akretion <http://www.akretion.com>
#   @author Magno Costa <magno.costa@akretion.com>
# Copyright (C) 2021 - TODAY Luis Felipe Miléo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api

SHADOWED_FIELDS = [
    'date_maturity',
    'company_id',
    'currency_id',
    'invoice_id',
]


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    _order = 'date_maturity, date desc, id desc'
    _inherits = {'l10n_br_fiscal.payment.line': 'fiscal_payment_line_id'}

    fiscal_document_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document',
        related='invoice_id.fiscal_document_id',
        store=True,
    )

    fiscal_payment_line_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.payment.line',
        string='Fiscal Payment Line',
        required=True,
        copy=False,
        ondelete='cascade',
    )

    @api.model
    def _shadowed_fields(self):
        """Returns the list of shadowed fields that are synced
        from the parent."""
        return SHADOWED_FIELDS

    @api.multi
    def _prepare_shadowed_fields_dict(self, default=False):
        self.ensure_one()
        vals = self._convert_to_write(self.read(self._shadowed_fields())[0])
        if default:  # in case you want to use new rather than write later
            return {"default_%s" % (k,): vals[k] for k in vals.keys()}
        return vals

    @api.model
    def create(self, values):
        dummy_payment_line_id = self.env.ref(
            'l10n_br_fiscal.fiscal_payment_line_dummy').id
        dummy_doc_id = self.env.ref('l10n_br_fiscal.fiscal_document_dummy').id
        fiscal_doc_id = self.env['account.invoice'].browse(
            values['invoice_id']).fiscal_document_id.id

        account_id = self.env['account.account'].browse(values['account_id'])

        if dummy_doc_id == fiscal_doc_id or not account_id.reconcile:
            values['fiscal_payment_line_id'] = dummy_payment_line_id
        aml = super().create(values)
        if dummy_doc_id != fiscal_doc_id and account_id.reconcile:
            shadowed_fiscal_vals = aml._prepare_shadowed_fields_dict()
            doc_id = aml.invoice_id.fiscal_document_id.id
            shadowed_fiscal_vals['document_id'] = doc_id
            aml.fiscal_payment_line_id.write(shadowed_fiscal_vals)
        return aml

    @api.multi
    def write(self, values):
        dummy_payment_line_id = self.env.ref(
            'l10n_br_fiscal.fiscal_payment_line_dummy')
        if values.get('invoice_id'):
            values['document_id'] = self.env[
                "account.invoice"].browse(
                values['invoice_id']).fiscal_document_id.id
        result = super().write(values)
        for aml in self:
            if aml.fiscal_payment_line_id != dummy_payment_line_id:
                shadowed_fiscal_vals = aml._prepare_shadowed_fields_dict()
                aml.fiscal_payment_line_id.write(shadowed_fiscal_vals)
        return result

    @api.multi
    def unlink(self):
        dummy_payment_line_id = self.env.ref(
            'l10n_br_fiscal.fiscal_payment_line_dummy').id
        unlink_fiscal_payment_lines = self.env['l10n_br_fiscal.payment.line']
        for record in self:
            if not record.exists():
                continue
            if record.fiscal_payment_line_id.id != dummy_payment_line_id:
                unlink_fiscal_payment_lines |= record.fiscal_document_line_id
        result = super().unlink()
        unlink_fiscal_payment_lines.unlink()
        self.clear_caches()
        return result
