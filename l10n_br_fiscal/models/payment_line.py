# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FiscalPaymentLine(models.Model):
    _name = 'l10n_br_fiscal.payment.line'
    _description = 'Fiscal Payment Line'

    _order = 'document_id, date_maturity'

    document_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document',
        string='Documento',
        related='payment_id.document_id',
        store=True,
    )
    payment_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.payment',
        string='Pagamento',
        ondelete='cascade',
        required=True,
    )
    communication = fields.Char(
        string='Número',
    )
    date_maturity = fields.Date(
        string='Data de vencimento',
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.user.company_id.currency_id
    )
    amount = fields.Monetary(
        string='Valor',
        required=True,
    )
