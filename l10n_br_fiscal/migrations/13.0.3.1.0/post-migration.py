
from openupgradelib import openupgrade

@openupgrade.migrate()
def migrate(env, version):
    # Verificar se a coluna existe
    if openupgrade.column_exists(env.cr, 'l10n_br_fiscal_cest', 'tax_definition_ids'):
        # Remover a coluna do banco de dados
        openupgrade.drop_columns(env.cr, [
            ('l10n_br_fiscal_cest', 'tax_definition_ids'),
        ])