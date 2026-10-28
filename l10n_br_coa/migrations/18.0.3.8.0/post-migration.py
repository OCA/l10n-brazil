# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Add the deductible ICMS ST of the sale to existing companies.

The ICMS ST of the sale was shipped without account and without the
deductible pair that the own ICMS has. With an operation that uses deductible
taxes the product line already carries the ST, so the ST tax line added it a
second time to the receivable: the title was bigger than the invoice total.

This version adds `tax_template_icms_st_out_deductible` to the chart and
gives the two taxes their accounts. A database where the chart was loaded
before gets them here, with the rules of the 18.0.3.7.0 script (the same
helper is reused): a deductible ICMS ST that somebody created by hand is kept
and only gets the xmlid, and the ICMS ST of the sale gets its account only
when it has none.
"""

import importlib.util
from pathlib import Path

from openupgradelib import openupgrade

TAXES = ["tax_template_icms_st_out_deductible"]
TAXES_WITHOUT_ACCOUNT = ["tax_template_out_icms_subist"]


def _load_migration_18_0_3_5_0():
    """The 18.0.3.7.0 script, loaded by path.

    The folder is named after the version and the file has a dash: neither is
    a valid module name, so a plain `import` cannot reach it.
    """
    path = Path(__file__).resolve().parents[1] / "18.0.3.7.0" / "post-migration.py"
    spec = importlib.util.spec_from_file_location(
        "l10n_br_coa_post_migration_18_0_3_5_0", path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def migrate_companies(env):
    _load_migration_18_0_3_5_0().migrate_companies(
        env,
        tax_groups=[],
        taxes=TAXES,
        taxes_without_account=TAXES_WITHOUT_ACCOUNT,
    )


@openupgrade.migrate()
def migrate(env, version):
    migrate_companies(env)
