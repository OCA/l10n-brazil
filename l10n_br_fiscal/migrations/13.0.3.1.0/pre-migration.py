from openupgradelib import openupgrade

@openupgrade.migrate()
def migrate(env, version):
    if not openupgrade.column_exists(env.cr, 'l10n_br_fiscal_cfop', 'destination'):
        env.cr.execute("ALTER TABLE l10n_br_fiscal_cfop ADD COLUMN destination varchar;")
    
    env.cr.execute("""
        UPDATE l10n_br_fiscal_cfop 
        SET destination = CASE 
            WHEN SUBSTRING(code, 1, 1) IN ('1', '5') THEN '1'
            WHEN SUBSTRING(code, 1, 1) IN ('2', '6') THEN '2'
            WHEN SUBSTRING(code, 1, 1) IN ('3', '7') THEN '3'
            ELSE NULL
        END
        WHERE destination IS NULL;
    """)
