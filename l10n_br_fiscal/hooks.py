# Copyright 2025-TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo import SUPERUSER_ID, api


def fill_missing_xml_ids(env):
    """
    Backfill missing ir.model.data (XML IDs) for manually created records
    in every model that inherits l10n_br_fiscal.data.editable.mixin and
    implements _get_xml_id_name(). This ensures that manual records are
    tracked and can be properly updated or preserved during future module
    updates.

    This helper can also be called from a migration script when deploying
    the mixin on an existing database (post_init_hook only runs at install).
    """
    mixin = env["l10n_br_fiscal.data.editable.mixin"]
    for model_name in env.registry:
        model = env[model_name]
        if (
            model._auto
            and not model._abstract
            and isinstance(model, type(mixin))
            # skip models that don't implement their own naming convention:
            and type(model)._get_xml_id_name is not type(mixin)._get_xml_id_name
        ):
            model.fill_missing_xml_ids()


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    fill_missing_xml_ids(env)
