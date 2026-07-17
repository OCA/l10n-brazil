# Copyright 2026 - TODAY Akretion (<https://akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """Copy the legacy crm.lead cnpj/cpf fields into vat.

    The l10n_br_crm refactor removes the dedicated ``cnpj`` and ``cpf``
    columns in favor of the standard ``vat`` field. Before those columns
    are dropped, migrate any existing data into ``vat`` without mask
    characters so the new computed ``vat_formatted_cnpj`` field works
    correctly.
    """
    env.cr.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'crm_lead'
          AND column_name IN ('cnpj', 'cpf')
        """
    )
    columns = {row[0] for row in env.cr.fetchall()}
    if not columns:
        return

    cnpj_expr = "cnpj" if "cnpj" in columns else "''"
    cpf_expr = "cpf" if "cpf" in columns else "''"

    openupgrade.logged_query(
        env.cr,
        f"""
        UPDATE crm_lead
        SET vat = regexp_replace(
            COALESCE(NULLIF({cnpj_expr}, ''), NULLIF({cpf_expr}, '')),
            '[./-]',
            '',
            'g'
        )
        WHERE (vat IS NULL OR vat = '')
          AND (NULLIF({cnpj_expr}, '') IS NOT NULL
               OR NULLIF({cpf_expr}, '') IS NOT NULL)
        """,
    )
