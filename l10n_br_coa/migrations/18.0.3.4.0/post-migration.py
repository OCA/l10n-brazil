# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Put the outstanding accounts on the payment method lines of the bank and
cash journals of the companies already loaded, and classify them. Only the
lines without an account are touched."""

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    companies = env["res.company"].search(
        [("chart_template", "in", ("br_oca", "br_oca_generic"))]
    )
    for company in companies:
        env["account.chart.template"]._l10n_br_setup_outstanding_accounts(company)
