# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Write the ICMS ST and FCP group accounts in companies with the chart."""
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    env["account.chart.template"]._complete_sale_deductible_taxes()
