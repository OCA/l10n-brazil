# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>

from odoo import fields, models


class ImportAddition(models.Model):
    _name = "l10n_br_trade_import.addition"
    _description = "Import Addition"

    import_declaration_id = fields.Many2one(
        comodel_name="l10n_br_trade_import.declaration",
        string="Import Declaration",
        required=True,
    )

    import_declaration_number = fields.Char(
        string="DI Number",
        related="import_declaration_id.document_number",
        help="Number of Import Declaration",
    )

    import_declaration_date = fields.Date(
        string="DI Date",
        related="import_declaration_id.document_date",
        help="Date of Import Declaration",
    )

    addition_number = fields.Char(
        string="Number", required=True, help="Number of Import Addition"
    )

    addtion_sequence = fields.Integer(
        string="Sequence",
        required=True,
        help="Sequential number of the item within the Addition",
    )

    manufacturer_id = fields.Many2one(
        comodel_name="res.partner",
        required=True,
        help="Foreign Manufacturer",
    )

    discount_value = fields.Float(
        string="Discount", help="Discount value of the DI item - Addition"
    )

    drawback = fields.Char(string="Drawback", help="Drawback concession act number")
