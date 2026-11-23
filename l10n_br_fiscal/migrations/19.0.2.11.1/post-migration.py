# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""The NBS CSV is loaded with noupdate, so an installed database never gets
the operation indicator added to it: carry it to the NBS already installed
(only where empty) and recompute the products that follow their NBS."""

import csv

from openupgradelib import openupgrade

from odoo.tools import file_open


@openupgrade.migrate()
def migrate(env, version):
    with file_open("l10n_br_fiscal/data/l10n_br_fiscal.nbs.csv") as csv_file:
        for row in csv.DictReader(csv_file):
            indicator_xmlid = row.get("operation_indicator_id/id")
            if not indicator_xmlid:
                continue
            nbs = env.ref(f"l10n_br_fiscal.{row['id']}", raise_if_not_found=False)
            indicator = env.ref(
                f"l10n_br_fiscal.{indicator_xmlid}", raise_if_not_found=False
            )
            if nbs and indicator and not nbs.operation_indicator_id:
                nbs.operation_indicator_id = indicator
    products = env["product.template"].search(
        [
            ("nbs_id.operation_indicator_id", "!=", False),
            ("operation_indicator_id", "=", False),
        ]
    )
    env.add_to_compute(products._fields["operation_indicator_id"], products)
    env.flush_all()
