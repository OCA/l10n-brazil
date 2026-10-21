# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    taxes = env.ref("l10n_br_coa.account_tag_dva_taxes")
    inputs = env.ref("l10n_br_coa.account_tag_dva_inputs")
    dropped = {f"coa_generic_6113{n:02}": taxes for n in range(1, 10)}
    for name in ("311991", "312991", "511701", "511702"):
        dropped[f"coa_generic_{name}"] = inputs
    env.ref(
        "l10n_br_coa_generic.l10n_br_coa_generic_template"
    )._update_company_accounts(dropped)
