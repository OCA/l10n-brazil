# Copyright (C) 2026 Luis Felipe Mileo - KMEE <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
"""ECF validation: what the generic SPED validator cannot reach.

Adds to the structural validator of ``l10n_br_sped_base`` the rules that
belong to this declaration: the registers required by the tax regime
declared in the 0010, and the **block P arithmetic**, where every computed
line is recomputed with the official formula published by the Brazilian
Federal Revenue from the editable lines of the file itself.
"""

from odoo.addons.l10n_br_sped_base.models.validator import SpedValidator, _decimal

from .apuracao_presumido import ApuracaoPresumido, arredonda

# Registers required from companies under the presumed profit regime with
# accounting bookkeeping (0010.FORMA_TRIB = 5 and 0010.TIP_ESC_PRE = "C").
PRESUMIDO_REQUIRED = [
    "0000",
    "0010",
    "0020",
    "0030",
    "0930",
    "J050",
    "K030",
    "P030",
]

# Block P registers that carry dynamic table lines.
VALUE_REGISTERS = ["P200", "P300", "P400", "P500"]


class EcfValidator(SpedValidator):
    """The SPED validator with the rules specific to the ECF."""

    def _validate_specific(self, structure):
        self._validate_required(structure)
        self._validate_block_p(structure)

    def _validate_block_p(self, structure):
        """The computed block P lines match the official formulas."""
        # the engine parameters come from the file ITSELF: the period from
        # the P030 (company opened or split mid-quarter has a broken period,
        # and the IRPJ surtax threshold is per month) and the CSLL rate from
        # the 0020; guessing a full quarter and a 9% rate would reject a
        # correct file
        csll_rate = "1"
        for _number, code, fields in structure:
            if code == "0020" and len(fields) > 1 and fields[1]:
                csll_rate = fields[1]
                break
        periods = self._group_block_p(structure)
        for period, data in periods.items():
            registers = data["registers"]
            values = {
                name: {code: value for code, value, _number in lines}
                for name, lines in registers.items()
            }
            positions = {
                name: {code: number for code, _value, number in lines}
                for name, lines in registers.items()
            }
            engine = ApuracaoPresumido(
                meses_periodo=data["months"], ind_aliquota_csll=csll_rate
            )
            checks = [
                ("P200", "10", engine._p200_10, "P200"),
                ("P200", "26", engine._p200_26, "P200"),
                ("P300", "3", engine._p300_3, "P300"),
                ("P300", "4", engine._p300_4, "P300"),
                ("P300", "15", engine._p300_15, "P300"),
                ("P400", "6", engine._p400_6, "P400"),
                ("P400", "21", engine._p400_21, "P400"),
                ("P500", "2", engine._p500_2, "P500"),
                ("P500", "4", engine._p500_4, "P500"),
                ("P500", "13", engine._p500_13, "P500"),
            ]
            for register, line, formula, source in checks:
                if register not in values or line not in values[register]:
                    continue
                expected = arredonda(formula(values[source]))
                found = values[register][line]
                if abs(expected - found) > 0.005:
                    self._error(
                        positions[register][line],
                        register,
                        f"line {line} of period {period} states {found:.2f} "
                        f"and the official formula yields {expected:.2f}",
                    )
            self._check_transport(period, values, positions)

    def _check_transport(self, period, values, positions):
        """Lines that only carry over the value of another line (CA type)."""
        transports = [("P300", "1", "P200", "26"), ("P500", "1", "P400", "21")]
        for target, target_line, source, source_line in transports:
            if target not in values or target_line not in values[target]:
                continue
            if source not in values or source_line not in values[source]:
                continue
            expected = values[source][source_line]
            found = values[target][target_line]
            if abs(expected - found) > 0.005:
                self._error(
                    positions[target][target_line],
                    target,
                    f"line {target_line} of period {period} must carry over "
                    f"{source}({source_line}) = {expected:.2f} and states "
                    f"{found:.2f}",
                )

    def _group_block_p(self, structure):
        """Block P lines grouped by the P030 assessment period.

        Returns ``{period: {"registers": {...}, "months": n}}``, with the
        months computed from the dates of the P030 itself
        (|P030|DT_INI|DT_FIN|...).
        """
        periods = {}
        current = None
        for number, code, fields in structure:
            if code == "P030":
                current = fields[3] if len(fields) > 3 else str(number)
                periods[current] = {
                    "registers": {},
                    "months": self._months_from_p030(fields),
                }
            elif code in VALUE_REGISTERS and current is not None:
                if len(fields) < 4:
                    continue
                line, value = fields[1], fields[3]
                if not value:
                    continue
                periods[current]["registers"].setdefault(code, []).append(
                    (line, _decimal(value), number)
                )
        return periods

    @staticmethod
    def _months_from_p030(fields):
        """Months elapsed between DT_INI and DT_FIN of the P030 (ddmmyyyy)."""
        try:
            start, end = fields[1], fields[2]
            years = int(end[4:8]) - int(start[4:8])
            return years * 12 + int(end[2:4]) - int(start[2:4]) + 1
        except (IndexError, ValueError):
            return 3

    def _validate_required(self, structure):
        """Registers required by the tax regime declared in the 0010."""
        codes = {code for _number, code, _fields in structure}
        register_0010 = [f for _n, code, f in structure if code == "0010"]
        if not register_0010:
            self._error(0, "0010", "the tax parameters register is missing")
            return
        # |0010|HASH_ECF_ANTERIOR|OPT_REFIS|FORMA_TRIB|...
        fields_0010 = register_0010[0]
        forma_trib = fields_0010[3] if len(fields_0010) > 3 else ""
        if forma_trib not in ("5", "6", "7", "8"):
            # only the presumed profit regime has its register set checked
            return
        for required in PRESUMIDO_REQUIRED:
            if required not in codes:
                self._error(
                    0,
                    required,
                    "register required for the presumed profit regime is " "missing",
                )
        for register in VALUE_REGISTERS:
            if register not in codes:
                self._error(
                    0,
                    register,
                    "the presumed profit assessment requires this register",
                )
