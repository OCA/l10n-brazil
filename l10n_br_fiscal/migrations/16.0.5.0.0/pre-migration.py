# Copyright (C) 2025 - Raphaël Valyi - Akretion <raphael.valyi@akretion.com.br>
# Copyright (C) 2025 - Antônio S. Pereira Neto - Engenere <neto@engenere.one>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # move data
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO uom_alias (uom_id, code, write_uid, create_uid, write_date,
         create_date)
        SELECT uom_id, code, write_uid, create_uid, write_date, create_date
        FROM uom_uom_alternative
        """,
    )
    # update xmlids
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE ir_model_data AS imd
        SET model  = 'uom.alias',
            res_id = new_alias.id
        FROM uom_uom_alternative AS old_alias
        JOIN uom_alias AS new_alias
            ON new_alias.code = old_alias.code
        WHERE imd.model = 'uom.uom.alternative'
        AND imd.res_id = old_alias.id
        """,
    )
