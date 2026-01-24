# Copyright (C) 2025  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    sql_query = """
        UPDATE l10n_br_fiscal_document
        SET state_edoc = CASE state_edoc
            WHEN 'em_digitacao' THEN 'draft'
            WHEN 'autorizada' THEN 'open'
            WHEN 'cancelada' THEN 'cancel'
            -- Importante: mantém o valor se não houver mapeamento
            -- os outros valores são tratados no script de migração
            -- do módulo l10n_br_fiscal_edi
            ELSE state_edoc
        END
        WHERE state_edoc IN (
            'em_digitacao', 'autorizada',
            'cancelada'
        );
    """
    openupgrade.logged_query(env.cr, sql_query)
