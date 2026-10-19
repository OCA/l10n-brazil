# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Create the deductible ICMS ST tax in companies that already loaded the chart."""
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    env["account.chart.template"]._complete_icms_st()
