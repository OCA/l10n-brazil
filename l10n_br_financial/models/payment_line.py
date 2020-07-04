# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class FiscalPaymentLine(models.Model):

    _inherit = 'l10n_br_fiscal.payment.line'

    def prepare_financial_move(self):

        result = []

        for record in self:
            result.append((0, 0, {
                'document_id': record.document_id.id,
                'date_maturity': record.date_maturity,
                'amount': record.amount,
                'partner_id': record.document_id.partner_id.id,
                'journal_id': record.document_id.journal_id.id,
                'payment_type': '2receive',
                'partner_type': 'customer',
                'payment_method_id': 1,
                'currency_id': record.currency_id.id,
                'payment_date': record.document_id.date,
                'company_id': record.company_id.id,
                'state': 'draft',
                'financial_account_id':
                    record.document_id.fiscal_operation_id.financial_account_id and
                    record.document_id.fiscal_operation_id.financial_account_id.id or False,
            }))
        return result
