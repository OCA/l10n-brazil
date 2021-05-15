# Copyright (C) 2021 - TODAY Raphael Valyi - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade
from odoo.addons.l10n_br_account.hooks import pre_init_hook


_column_copies = {
    'account_invoice': [
        ('fiscal_document_id', None, None)],
    }


@openupgrade.migrate()
def migrate(env, version):
    if (
            openupgrade.column_exists(
                env.cr,
                'account_invoice',
                'fiscal_document_id')
            ):
        openupgrade.copy_columns(env.cr, _column_copies)

        #  this is required to get the init_hook work:
        openupgrade.logged_query(
            env.cr,
            "alter table account_invoice drop column fiscal_document_id;"
        )

        pre_init_hook(env.cr)
        openupgrade.logged_query(
            env.cr,
            """
            DELETE from account_tax_template WHERE id IN (
            SELECT res_id from ir_model_data
            WHERE model='account.tax.template'
            AND NOT module ilike 'l10n_br_coa%')
            """
        )
