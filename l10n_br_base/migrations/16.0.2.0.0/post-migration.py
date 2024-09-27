# Copyright 2024 - TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    brazil_id = env.ref("base.br").id
    openupgrade.logged_query(
        env.cr,
        f"""
        UPDATE res_partner
        SET
            l10n_br_cpf_code = CASE
                WHEN length(regexp_replace(vat, '[^0-9]', '', 'g')) = 11 THEN vat
                ELSE l10n_br_cpf_code
            END,
            vat = CASE
                WHEN length(regexp_replace(vat, '[^0-9]', '', 'g')) = 11 THEN ''
                ELSE vat
            END
        WHERE country_id={brazil_id}
        AND length(regexp_replace(vat, '[^0-9]', '', 'g')) = 11
        """,
    )
