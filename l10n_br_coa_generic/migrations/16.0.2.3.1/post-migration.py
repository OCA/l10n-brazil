# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Write the accounts of the ICMS ST group in the companies that loaded the chart.

The group now declares 2.1.7.1.11, 6.1.1.2.07 and 6.1.1.2.27. Companies that
loaded the chart before have the ICMS ST of the sale without account and, if the
l10n_br_coa script did not run, without the deductible pair. Both are completed
here, never overwriting an account already set. Idempotent.
"""
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    env["account.chart.template"]._complete_icms_st()
