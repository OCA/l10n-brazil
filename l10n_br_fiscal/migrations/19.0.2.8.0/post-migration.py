# Copyright 2026 Engenere - Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """Recompute the annex of the main activity of every company: the
    previous computation crashed or left stale values in several cases."""
    companies = env["res.company"].with_context(active_test=False).search([])
    for fname in ("simplified_tax_id", "simplified_tax_range_id", "coefficient_r"):
        env.add_to_compute(companies._fields[fname], companies)
    env.flush_all()
