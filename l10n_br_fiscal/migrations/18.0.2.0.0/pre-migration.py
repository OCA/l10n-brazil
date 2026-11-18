# Copyright (C) 2025 - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """Rename product.template M2M field to the new pluralized name.

    The underlying Many2many relation table remains the same because
    Odoo derives it from model table names, not the field name. This
    rename keeps references (e.g., stored views/filters) consistent.
    """
    openupgrade.rename_fields(
        env,
        [
            (
                "product.template",
                "product.template",
                "city_taxation_code_id",
                "city_taxation_code_ids",
            ),
        ],
    )
