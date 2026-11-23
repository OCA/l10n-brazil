# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def pre_init_hook(cr):
    """Create the column of the review state of the document by hand.

    The field is stored and computed from the lines. Left to the ORM, the installation
    would compute it for every document of the database, a loop over the whole table;
    only an imported document has a review state, and the documents that exist are not.
    """
    cr.execute(
        "ALTER TABLE l10n_br_fiscal_document "
        "ADD COLUMN IF NOT EXISTS import_state VARCHAR"
    )
