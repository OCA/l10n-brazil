# Copyright (C) 2021 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    SITUACAO_EDOC_AUTORIZADA,
    DOCUMENT_ISSUER_COMPANY,
)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _prepare_wh_invoice(self, move_line, fiscal_tax_group):
        wh_date_invoice = fields.Date.context_today(self)
        wh_due_invoice = wh_date_invoice.replace(
            day=fiscal_tax_group.wh_due_day)
        values = {
            'partner_id': fiscal_tax_group.partner_id.id,
            'date_invoice': wh_date_invoice,
            'date_due': wh_due_invoice + relativedelta(months=1),
            'type': 'in_invoice',
            'journal_id': move_line.journal_id.id,
            'origin': move_line.invoice_id.number, # TODO
        }
        return values

    def _prepare_wh_invoice_line(self, invoice, move_line, fiscal_tax_group):
        values = {
            'name': move_line.name,
            'quantity': 1.0,
            'price_unit': abs(move_line.balance),
            'invoice_id': invoice.id,
            'account_id': move_line.account_id.id,
            'account_analytic_id': move_line.analytic_account_id.id,
        }
        return values

    def create_wh_invoice(self):
        for move in self:
            for line in move.line_ids.filtered(lambda l: l.tax_line_id):
                account_tax_group = line.tax_line_id.tax_group_id
                if account_tax_group and account_tax_group.fiscal_tax_group_id:
                    fiscal_group = account_tax_group.fiscal_tax_group_id
                    if fiscal_group.tax_withholding:
                        invoice = self.env['account.invoice'].create(
                            self._prepare_wh_invoice(line, fiscal_group))

                        self.env['account.invoice.line'].create(
                            self._prepare_wh_invoice_line(
                                invoice, line, fiscal_group))

                        invoice.action_invoice_open()

    def create_deductible_lines(self):
        pass

    def post(self, invoice=False):
        dummy_doc = self.env.ref('l10n_br_fiscal.fiscal_document_dummy')
        result = super().post(invoice)
        self.create_wh_invoice()
        self.create_deductible_lines()
        if invoice:
            if (invoice.fiscal_document_id != dummy_doc
                    and invoice.document_electronic
                    and invoice.issuer == DOCUMENT_ISSUER_COMPANY
                    and invoice.state_edoc != SITUACAO_EDOC_AUTORIZADA):
                self.button_cancel()
        return result
