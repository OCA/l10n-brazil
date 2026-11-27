# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    """The lines of a document imported by the old wizard have no review state.

    The wizard was the review: its grid chose the product, the unit and the factor
    before the document existed. The documents it left are reviewed already, so
    their lines are resolved, and the invoice of one that has none yet can be
    generated from the new screen, which only accepts resolved lines.
    """
    cr.execute(
        """
        UPDATE l10n_br_fiscal_document_line line
           SET import_state = 'resolved'
          FROM l10n_br_fiscal_document document
         WHERE line.document_id = document.id
           AND document.imported_document
           AND line.import_state IS NULL
        """
    )
