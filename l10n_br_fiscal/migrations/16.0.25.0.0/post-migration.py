# Copyright 2026 Engenere - Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """Give the companies already under the Simples Nacional their effective
    tax lines, otherwise they would grant no ICMS credit until someone saves
    their tax framework again."""
    env["res.company"].with_context(active_test=False).search(
        []
    )._update_effective_tax_lines()
