# Copyright (C) 2026 - TODAY, KMEE (<https://kmee.com.br>)
# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class L10nBrDuimpAdditionDeduction(models.Model):
    _name = "l10n_br_duimp.addition.deduction"
    _inherit = "l10n_br_duimp.mixin"
    _description = "DUIMP Addition/Deduction"

    declaration_id = fields.Many2one(
        comodel_name="l10n_br_duimp.declaration",
        related="item_id.declaration_id",
        store=True,
    )

    item_id = fields.Many2one(
        comodel_name="l10n_br_duimp.item",
        string="Item",
        required=True,
        ondelete="cascade",
    )

    code = fields.Char()
    description = fields.Char()

    trade_currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Negotiated Currency",
    )
    company_currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="declaration_id.currency_id",
    )

    amount = fields.Monetary(
        string="Amount (BRL)",
        currency_field="company_currency_id",
        help="Amount already converted to BRL. Positive for an addition, "
        "negative for a deduction.",
    )
    trade_currency_amount = fields.Monetary(
        string="Amount (Currency)",
        currency_field="trade_currency_id",
    )
    exchange_rate = fields.Float(digits=(12, 8))
