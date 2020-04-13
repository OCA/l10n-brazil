# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class FiscalPaymentLine(models.Model):

    _inherit = 'l10n_br_fiscal.payment.line'

    def generate_move(self, move_lines):
        for record in self:
            if record.amount:
                data = {
                    'name': '/',
                    'debit': record.amount,
                    'currency_id':
                        record.currency_id and record.currency_id.id or False,
                    'partner_id': record.document_id.partner_id and record.document_id.partner_id.id or False,
                    'account_id': record.document_id.partner_id.property_account_receivable_id.id,
                    'date_maturity': record.date_maturity,
                }
                move_lines.append((0, 0, data))
