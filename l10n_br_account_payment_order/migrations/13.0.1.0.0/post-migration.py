# Copyright 2023 Engenere - Antônio S. P. Neto
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    update_cnab_return_event_invoice_relation(env.cr)


def update_cnab_return_event_invoice_relation(cr):
    openupgrade.logged_query(
        cr,
        """
        UPDATE l10n_br_cnab_return_event cre
        SET invoice_id = am.id
        FROM account_move am
        WHERE cre.{old_inv_line_id} = am.old_invoice_id
        """.format(
            old_inv_line_id=openupgrade.get_legacy_name("invoice_id")
        ),
    )
