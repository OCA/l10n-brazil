# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re
import unicodedata

# Limits of xCorrecao in the official e110110 schema (NT 2011/003).
CORRECTION_MIN_LENGTH = 15
CORRECTION_MAX_LENGTH = 1000

# Typographic characters commonly pasted from word processors and chat apps
# mapped to the closest keyboard equivalent. Escapes are used on purpose.
_CORRECTION_CHAR_MAP = {
    "\U00002018": "'",
    "\U00002019": "'",
    "\U0000201a": "'",
    "\U0000201b": "'",
    "\U00002032": "'",
    "\U0000201c": '"',
    "\U0000201d": '"',
    "\U0000201e": '"',
    "\U0000201f": '"',
    "\U000000ab": '"',
    "\U000000bb": '"',
    "\U00002033": '"',
    "\U00002010": "-",
    "\U00002011": "-",
    "\U00002012": "-",
    "\U00002013": "-",
    "\U00002014": "-",
    "\U00002015": "-",
    "\U00002212": "-",
    "\U00002022": "-",
    "\U00002026": "...",
    "\U000020ac": "EUR",
    "\U0000200b": "",
    "\U0000200c": "",
    "\U0000200d": "",
    "\U0000feff": "",
    "\U000000ad": "",
}

_WHITESPACE_RE = re.compile(r"\s+")


def _is_blank(char):
    # C0/C1 controls (tab, newline, DEL...) and every kind of space separator
    return unicodedata.category(char) in ("Cc", "Zs", "Zl", "Zp")


def normalize_correction_text(text):
    """Make the text of a correction letter acceptable by the e110110 schema.

    Typographic punctuation becomes its keyboard equivalent, tabs, line breaks
    and control characters become spaces, runs of spaces collapse and the
    result is stripped (the schema forbids a space at either end).

    Returns a tuple ``(normalized_text, invalid_chars)``. ``invalid_chars``
    lists what is still outside the range U+0020 to U+00FF accepted by the
    schema; such characters are kept in the text so the caller can refuse it
    instead of silently changing its meaning.
    """
    result = []
    invalid = []
    for char in text or "":
        char = _CORRECTION_CHAR_MAP.get(char, char)
        for item in char:
            if _is_blank(item):
                result.append(" ")
            elif ord(item) <= 0xFF:
                result.append(item)
            else:
                # e.g. full width letters; NFKC is applied per character so
                # that valid Latin-1 signs such as the ordinal indicators
                # are never rewritten.
                folded = unicodedata.normalize("NFKC", item)
                if folded != item and all(0x20 <= ord(c) <= 0xFF for c in folded):
                    result.append(folded)
                else:
                    result.append(item)
                    if item not in invalid:
                        invalid.append(item)
    normalized = _WHITESPACE_RE.sub(" ", "".join(result)).strip()
    return normalized, [c for c in invalid if c in normalized]
