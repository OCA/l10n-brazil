# Copyright 2026 KMEE (Ygor Carvalho <ygor.carvalho@kmee.com.br>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase

FIXO = "ISENCAO DO ICMS, REGIME ESPECIAL 91092 2020, CONTRATO A-005446"


class TestComment(TransactionCase):
    def _comment(self, comment):
        return self.env["l10n_br_fiscal.comment"].create(
            {
                "name": "comment test",
                "comment": comment,
                "comment_type": "commercial",
                "object": "l10n_br_fiscal.document.mixin",
            }
        )

    def test_a_comment_that_does_not_apply_leaves_no_separator(self):
        """A comment that renders to nothing must not join the message.

        A benefit legend tied to a contract belongs to the notes of that
        customer only, so the comment is written conditional on the document.
        For every other document it renders to nothing, and joining that empty
        render used to leave the manual text ending in " - " on the DANFE.
        """
        comment = self._comment(f"% if doc.applies:\n{FIXO}\n% endif")

        message = comment.compute_message(
            {"doc": type("Doc", (), {"applies": False})()}, "ITEM 01.05"
        )

        self.assertEqual(message, "ITEM 01.05")

    def test_a_comment_that_applies_comes_after_the_manual_text(self):
        comment = self._comment(f"% if doc.applies:\n{FIXO}\n% endif")

        message = comment.compute_message(
            {"doc": type("Doc", (), {"applies": True})()}, "ITEM 01.05"
        )

        self.assertEqual(message, f"ITEM 01.05 - {FIXO}")
