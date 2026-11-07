# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Create the deductible ICMS ST of the sale in the companies that loaded the chart.

The tax is new in this version and a template only reaches a company when the
chart is loaded into it. The accounts of the ST group come with the chart that
declares them (see the script of l10n_br_coa_generic). Idempotent.
"""
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    env["account.chart.template"]._complete_icms_st()
