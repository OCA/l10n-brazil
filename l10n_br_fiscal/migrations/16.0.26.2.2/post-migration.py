# Copyright 2025-TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

from odoo.addons.l10n_br_fiscal.hooks import fill_missing_xml_ids


@openupgrade.migrate()
def migrate(env, version):
    """Backfill the ir.model.data entries of the records created by hand.

    The post_init_hook only runs when the module is installed, so the records
    added by hand on a database already running l10n_br_fiscal would stay
    without xml_id, and a later data file update would then create a
    duplicate in place of updating them. Bumping the module version and
    calling the very same helper here covers the other case: the database
    that already has the localization installed.
    """
    fill_missing_xml_ids(env)
