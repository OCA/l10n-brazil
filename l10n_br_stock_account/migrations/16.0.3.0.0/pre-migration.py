# Copyright (C) 2025 - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    field_spec = [
        (
            "stock.picking",
            "stock_picking",
            "amount_untaxed",
            "fiscal_amount_untaxed",
        ),
        (
            "stock.picking",
            "stock_picking",
            "amount_tax",
            "fiscal_amount_tax",
        ),
        (
            "stock.picking",
            "stock_picking",
            "amount_total",
            "fiscal_amount_total",
        ),
    ]

    openupgrade.rename_fields(env, field_spec)
