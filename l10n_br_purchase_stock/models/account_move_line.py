# Copyright (C) 2026  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def _get_bill_matching_reference_sql(self, alias):
        """
        Duck-typing hook picked up dynamically by `stock_picking_bill_matching`.
        The `alias` argument (e.g., 'aml' or 'sm') is passed by the SQL view builder.
        """
        return (
            f"NULLIF(COALESCE({alias}.partner_order, '') || '-' "
            f"|| COALESCE({alias}.partner_order_line, ''), '-')"
        )
