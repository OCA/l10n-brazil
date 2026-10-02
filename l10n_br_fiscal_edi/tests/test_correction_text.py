# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from odoo.exceptions import UserError
from odoo.tests import TransactionCase

from ..tools import normalize_correction_text

# xCorrecao pattern of the e110110 schema
LDQ, RDQ = "\U0000201c", "\U0000201d"
ENDASH, EMDASH, ELLIPSIS = "\U00002013", "\U00002014", "\U00002026"
XSD_PATTERN = re.compile("^(?:[!-ÿ][ -ÿ]*[!-ÿ]|[!-ÿ])$")


class TestCorrectionText(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.document = cls.env["l10n_br_fiscal.document"]

    def test_normalization_table(self):
        cases = {
            "plain text stays": "plain text stays",
            # curly quotes, en dash, em dash and ellipsis pasted from Word
            f"Onde se lê {LDQ}transp{RDQ} {ENDASH} leia{EMDASH}se{ELLIPSIS}": (
                'Onde se lê "transp" - leia-se...'
            ),
            "it\U00002019s the \U00002018new\U00002019 one": "it's the 'new' one",
            # tab, line breaks, carriage return and repeated spaces
            "line one\nline two\r\n\tline   three": "line one line two line three",
            # spaces at the ends are forbidden by the schema
            "   padded text here   ": "padded text here",
            # no-break space, zero width space and soft hyphen
            "a\U000000a0\U000000a0b\U0000200bc\U000000ad": "a bc",
            # Latin-1 signs valid in the schema must not be rewritten
            "nº 5 e 2ª via": "nº 5 e 2ª via",
            "\U000020ac10": "EUR10",
            # decomposed accents (NFD, e.g. pasted from macOS or a PDF)
            "Corre\U00000063\U00000327a\U00000303o": "Correção",
            # full width letters fold to ASCII
            "\U0000ff21\U0000ff22\U0000ff23": "ABC",
            "": "",
            None: "",
        }
        for raw, expected in cases.items():
            text, invalid = normalize_correction_text(raw)
            self.assertEqual(text, expected, repr(raw))
            self.assertFalse(invalid, repr(raw))
            if text:
                self.assertTrue(XSD_PATTERN.match(text), repr(raw))

    def test_characters_outside_schema_are_reported(self):
        text, invalid = normalize_correction_text("emoji \U0001f600 and \U00004e2d")
        self.assertEqual(invalid, ["\U0001f600", "\U00004e2d"])
        self.assertIn("\U0001f600", text)

    def test_document_refuses_bad_text_before_sending(self):
        for raw in (None, "", "   \n\t ", "x" * 14, "  " + "x" * 14 + "  "):
            with self.assertRaises(UserError, msg=repr(raw)):
                self.document._normalize_correction_text(raw)
        with self.assertRaises(UserError):
            self.document._normalize_correction_text("y" * 1001)
        with self.assertRaises(UserError):
            self.document._normalize_correction_text("valid text \U0001f600 here")

    def test_document_accepts_boundaries(self):
        self.assertEqual(self.document._normalize_correction_text("x" * 15), "x" * 15)
        self.assertEqual(
            self.document._normalize_correction_text("y" * 1000), "y" * 1000
        )
        # the limits apply after the normalization
        padded = "  " + "z" * 14 + "\n\n"
        with self.assertRaises(UserError):
            self.document._normalize_correction_text(padded)
