# Copyright (C) 2025 - Antônio S. Pereira Neto - Engenere <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """
    Safety net: copy the taxpayer ID from the custom `cnpj_cpf` column
    into the official `vat` field **only** when `vat` is still empty.

    In most databases both columns already match, but this prevents
    accidental data loss on installs where the two got out of sync.
    """

    cr = env.cr
    if not (
        openupgrade.column_exists(cr, "res_partner", "vat")
        and openupgrade.column_exists(cr, "res_partner", "cnpj_cpf")
    ):
        return  # nothing to do

    openupgrade.logged_query(
        cr,
        """
        UPDATE res_partner
           SET vat = cnpj_cpf
         WHERE vat IS NULL
           AND cnpj_cpf IS NOT NULL;
        """,
    )
