# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class FiscalPaymentLine(models.Model):
    _inherit = 'l10n_br_fiscal.payment.line'

    invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice',
        related='payment_id.invoice_id',
        store=True,
    )

    def generate_move(self, move_lines):
        for r in self:
            if r.amount:
                data = {
                    'name': '/',
                    'debit': r.amount,
                    # 'currency_id':
                    #     r.currency_id and r.currency_id.id or False,
                    # Só preencha a moeda caso o lançamento seja multi moeda.
                    'partner_id':
                        r.document_id.partner_id and
                        r.document_id.partner_id.id or False,
                    'account_id':
                        r.document_id.partner_id.property_account_receivable_id.id,
                    'date_maturity': r.date_maturity,
                }
                move_lines.append((0, 0, data))
