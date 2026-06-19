# Copyright (C) 2025 - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    field_spec = [
        (
            "sale.order",
            "sale_order",
            "amount_untaxed",
            "fiscal_amount_untaxed",
        ),
        (
            "sale.order",
            "sale_order",
            "amount_tax",
            "fiscal_amount_tax",
        ),
        (
            "sale.order",
            "sale_order",
            "amount_total",
            "fiscal_amount_total",
        ),
    ]
    openupgrade.rename_fields(env, field_spec)
