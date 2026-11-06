# Copyright (C) 2026 - TODAY, KMEE (<https://kmee.com.br>)
# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class L10nBrDuimpPayment(models.Model):
    _name = "l10n_br_duimp.payment"
    _description = "DUIMP Payment"

    declaration_id = fields.Many2one(
        comodel_name="l10n_br_duimp.declaration",
        string="Declaration",
        required=True,
        ondelete="cascade",
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="declaration_id.currency_id",
        readonly=True,
    )

    revenue_code = fields.Char()
    payment_type_name = fields.Char(string="Payment Type")

    bank_name = fields.Char(string="Bank")
    bank_branch = fields.Char(string="Branch")
    bank_account = fields.Char(string="Account")
    payment_date = fields.Date()
    amendment_number = fields.Char()

    revenue_amount = fields.Monetary()
    interest_amount = fields.Monetary(string="Interest/Charges")
    penalty_amount = fields.Monetary(string="Penalty")
