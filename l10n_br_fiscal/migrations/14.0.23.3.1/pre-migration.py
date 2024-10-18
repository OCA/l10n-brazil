from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """
    Script de migração para remover os campos das tabelas e
    ajustar o relacionamento com as estimativas de imposto.
    """

    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE l10n_br_fiscal_ncm DROP COLUMN IF EXISTS estimate_tax_national;
        ALTER TABLE l10n_br_fiscal_ncm DROP COLUMN IF EXISTS estimate_tax_imported;
        ALTER TABLE l10n_br_fiscal_nbs DROP COLUMN IF EXISTS estimate_tax_national;
        ALTER TABLE l10n_br_fiscal_nbs DROP COLUMN IF EXISTS estimate_tax_imported;
        """,
    )

    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE l10n_br_fiscal_tax_estimate DROP COLUMN IF EXISTS company_id;
        """,
    )

    models_to_update = ["l10n_br_fiscal.ncm", "l10n_br_fiscal.nbs"]
    for model_name in models_to_update:
        records = env[model_name].search([])
        for record in records:
            last_estimated = record.tax_estimate_ids.sorted(
                key="create_date", reverse=True
            )[:1]
            if last_estimated:
                last_estimated.write({"active": True})
                (record.tax_estimate_ids - last_estimated).write({"active": False})
