# Copyright (C) 2026 - TODAY, KMEE (<https://kmee.com.br>)
# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models

from ..constants.duimp import DUIMP_TAX_SEQUENCE, DUIMP_TAX_TYPE_SELECTION


class L10nBrDuimpItemTax(models.Model):
    _name = "l10n_br_duimp.item.tax"
    _description = "DUIMP Item Tax"
    _order = "item_id, sequence, type"

    item_id = fields.Many2one(
        comodel_name="l10n_br_duimp.item",
        string="Item",
        required=True,
        ondelete="cascade",
    )

    declaration_id = fields.Many2one(
        comodel_name="l10n_br_duimp.declaration",
        related="item_id.declaration_id",
        store=True,
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="declaration_id.currency_id",
    )

    type = fields.Selection(
        selection=DUIMP_TAX_TYPE_SELECTION,
        required=True,
    )

    sequence = fields.Integer(
        compute="_compute_sequence",
        store=True,
        help="Assessment order, so the breakdown is not listed "
        "alphabetically by tax code.",
    )

    @api.depends("type")
    def _compute_sequence(self):
        for record in self:
            record.sequence = DUIMP_TAX_SEQUENCE.get(record.type, 99)

    regime_code = fields.Char()
    legal_basis_code = fields.Char(
        help="memoriaCalculo.fundamentosAplicados[].fundamento.",
    )
    cst = fields.Char(
        string="CST",
        help="Tax situation code, returned for the tax reform taxes "
        "(CBS/IBS); the older federal taxes come without it.",
    )
    cclass_trib = fields.Char(string="cClassTrib")

    tax_base = fields.Monetary()
    ad_valorem_rate = fields.Float(string="Rate (%)", digits=(12, 4))
    amount_due = fields.Monetary()
    amount_to_collect = fields.Monetary()
