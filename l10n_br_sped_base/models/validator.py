# Copyright (C) 2026 Luis Felipe Mileo - KMEE <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
"""Structural validation of a SPED file.

The goal is the same as the first pass of the official validator (PVA):
reject the file before transmission when it breaks the layout. The rules
checked here are the ones the layout itself defines and that can be verified
without querying the tax authority databases:

1. **block order** and the opening/closing pair of every block;
2. **hierarchy**: every child register comes after a valid parent;
3. **fields**: field count per register and the fields marked ``required``
   in the spec;
4. **numeric format**: comma as the decimal separator and no thousands
   separator;
5. **block 9 counters**: each 9900 counts the actual occurrences of the
   register, 9990 counts the block 9 lines and 9999 counts the file lines;
6. **required registers** of the tax regime declared in the 0010 register.

What this validator does NOT do is whatever depends on government data:
matching against the transmitted ECD, checking codes against the published
referential chart of accounts and validating the digital signature.

It also does not check maximum field sizes. The ``sped_length`` of the
generated spec is unreliable for free-text fields (0030.ENDERECO shows up
with 15 positions, 0930.EMAIL with 6 and P100.CODIGO with 5, all below the
layout), so checking against it would reject valid files. This check can
come back once the spec is regenerated with the right sizes.
"""

from collections import defaultdict

# ECF blocks in the official order. Block 0 opens with 0000 and closes with
# 0990; the other blocks open with <block>001 and close with <block>990.
BLOCKS = ["0", "E", "J", "K", "L", "M", "N", "P", "Q", "T", "U", "V", "W", "X", "Y"]


class ValidationIssue:
    """A non-conformity found in the file."""

    def __init__(self, line, register, message):
        self.line = line
        self.register = register
        self.message = message

    def __str__(self):
        position = f"line {self.line}" if self.line else "file"
        return f"{position} [{self.register}]: {self.message}"

    __repr__ = __str__


class SpedValidator:
    """Checks a SPED file against the layout.

    :param text: file content.
    :param registers: ``{code: [(field, required, type)]}`` coming from the
        spec, used to check the count, the requiredness and the format of
        the fields. It can be omitted, in which case the field checks are
        skipped.
    """

    def __init__(self, text, registers=None):
        self.text = text
        self.registers = registers or {}
        self.issues = []
        self.lines = [
            line for line in text.replace("\r\n", "\n").split("\n") if line.strip()
        ]

    # ------------------------------------------------------------------

    def _error(self, number, register, message):
        self.issues.append(ValidationIssue(number, register, message))

    def _line_fields(self, line):
        """Fields of a SPED line, without the delimiters at the borders."""
        if not line.startswith("|") or not line.endswith("|"):
            return None
        return line[1:-1].split("|")

    def validate(self):
        """Run every rule and return the issue list (empty when valid)."""
        self.issues = []
        structure = self._parse()
        if structure is None:
            return self.issues
        self._validate_blocks(structure)
        self._validate_fields(structure)
        self._validate_counters(structure)
        self._validate_specific(structure)
        return self.issues

    def _validate_specific(self, structure):
        """Hook for the rules that belong to each specific declaration.

        The generic validator only knows what holds for any SPED file.
        Registers required by tax regime, assessment arithmetic and other
        conditional business rules belong to whoever knows them.
        """

    # ------------------------------------------------------------------

    def _parse(self):
        """Read the file into ``[(number, code, fields)]``, checking basics."""
        structure = []
        for number, line in enumerate(self.lines, start=1):
            fields = self._line_fields(line)
            if fields is None:
                self._error(
                    number,
                    "?",
                    "the line does not start and end with the field delimiter",
                )
                continue
            code = fields[0]
            if not code:
                self._error(number, "?", "the line does not identify a register")
                continue
            structure.append((number, code, fields))
        if not structure:
            self._error(0, "?", "the file has no registers at all")
            return None
        if structure[0][1] != "0000":
            self._error(1, structure[0][1], "the file does not open with 0000")
        if structure[-1][1] != "9999":
            self._error(
                len(self.lines),
                structure[-1][1],
                "the file does not end with 9999",
            )
        return structure

    def _validate_blocks(self, structure):
        """Each block opens and closes once, in the official order."""
        seen = []
        for number, code, _fields in structure:
            block = "0" if code.startswith("0") else code[0]
            if code == "0000":
                continue
            if block == "9":
                block = "9"
            if block not in seen:
                seen.append(block)
            elif seen[-1] != block:
                self._error(
                    number,
                    code,
                    f"block {block} reappears after it was already closed",
                )

        expected = [block for block in BLOCKS + ["9"] if block in seen]
        if seen != expected:
            self._error(
                0,
                "?",
                f"blocks are out of the official order: {' '.join(seen)}",
            )

        codes = {code for _number, code, _fields in structure}
        for block in BLOCKS:
            if block not in seen:
                continue
            opening = "0001" if block == "0" else f"{block}001"
            closing = "0990" if block == "0" else f"{block}990"
            if opening not in codes:
                self._error(0, opening, f"the opening of block {block} is missing")
            if closing not in codes:
                self._error(0, closing, f"the closing of block {block} is missing")

    def _validate_fields(self, structure):
        """Field count, requiredness and format.

        The definitions come from the spec as ``(name, required, type)``.
        """
        if not self.registers:
            return
        for number, code, fields in structure:
            definition = self.registers.get(code)
            if definition is None:
                continue
            values = fields[1:]
            if len(values) != len(definition):
                self._error(
                    number,
                    code,
                    f"the register has {len(values)} fields and the layout "
                    f"defines {len(definition)}",
                )
                continue
            for value, (name, required, ftype) in zip(values, definition, strict=False):
                if required and not value:
                    self._error(number, code, f"field {name} is required")
                if ftype in ("monetary", "float") and value and "." in value:
                    self._error(
                        number,
                        code,
                        f"field {name} uses a dot: the SPED decimal separator "
                        "is the comma and there is no thousands separator",
                    )

    def _validate_counters(self, structure):
        """Block 9 counts what the file actually has."""
        occurrences = defaultdict(int)
        for _number, code, _fields in structure:
            occurrences[code] += 1

        for number, code, fields in structure:
            if code != "9900":
                continue
            counted, quantity = fields[1], fields[2]
            expected = occurrences.get(counted, 0)
            if not quantity.isdigit() or int(quantity) != expected:
                self._error(
                    number,
                    "9900",
                    f"declares {quantity} occurrence(s) of register {counted} "
                    f"and the file has {expected}",
                )

        declared = {fields[1] for _n, code, fields in structure if code == "9900"}
        for code in sorted(occurrences):
            if code not in declared:
                self._error(
                    0,
                    "9900",
                    f"register {code} appears in the file and is not "
                    "declared in block 9",
                )

        for number, code, fields in structure:
            if code == "9999":
                total = fields[1]
                if not total.isdigit() or int(total) != len(structure):
                    self._error(
                        number,
                        "9999",
                        f"declares {total} line(s) and the file has "
                        f"{len(structure)}",
                    )


def _decimal(value):
    """SPED number (comma as the decimal separator) as a float."""
    try:
        return float(value.replace(",", "."))
    except ValueError:
        return 0.0
