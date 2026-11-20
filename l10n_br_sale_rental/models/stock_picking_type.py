# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    l10n_br_rental_kind = fields.Selection(
        selection=[("remessa", "Rental Delivery"), ("retorno", "Rental Return")],
        string="Rental Transfer",
        help="Transfers of rented goods, invoiced as NF-e (remessa/retorno)"
        " without receivable.",
    )
