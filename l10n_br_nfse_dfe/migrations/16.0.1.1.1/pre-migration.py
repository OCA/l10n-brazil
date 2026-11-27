# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

XMLID_NAME = "field_res_company__nfse_import_product_id"


def migrate(cr, version):
    """The company field nfse_import_product_id moved to l10n_br_nfse.

    A field is deleted, with its column, when the module that owns its xmlid no
    longer declares it. The xmlid goes to l10n_br_nfse, or is dropped when
    l10n_br_nfse (which loads first on a full update) already has its own.
    """
    cr.execute(
        """
        DELETE FROM ir_model_data old
        USING ir_model_data new
        WHERE old.module = 'l10n_br_nfse_dfe'
          AND new.module = 'l10n_br_nfse'
          AND old.model = 'ir.model.fields'
          AND new.model = 'ir.model.fields'
          AND old.name = %(name)s
          AND new.name = %(name)s
        """,
        {"name": XMLID_NAME},
    )
    cr.execute(
        """
        UPDATE ir_model_data
           SET module = 'l10n_br_nfse'
         WHERE module = 'l10n_br_nfse_dfe'
           AND model = 'ir.model.fields'
           AND name = %(name)s
        """,
        {"name": XMLID_NAME},
    )
