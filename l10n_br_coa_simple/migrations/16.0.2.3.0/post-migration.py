# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    taxes = env.ref("l10n_br_coa.account_tag_dva_taxes")
    inputs = env.ref("l10n_br_coa.account_tag_dva_inputs")
    dropped = {f"account_template_31202{n:02}": taxes for n in range(1, 4)}
    for name in ("3320204", "3320205"):
        dropped[f"account_template_{name}"] = inputs
    env.ref(
        "l10n_br_coa_simple.l10n_br_coa_simple_chart_template"
    )._update_company_accounts(dropped)
