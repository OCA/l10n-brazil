# Copyright (C) 2026  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
"""Constants of the FCI (Ficha de Conteúdo de Importação) digital file.

Layout defined by the Anexo Único of the Ato COTEPE ICMS 61/2012 and
detailed in the "Manual Sistema FCI" published by SEFAZ/SP.
"""

# Field separator of every record of the file.
FCI_FIELD_SEPARATOR = "|"

# Register 0000, field VERSAO_LEIAUTE.
FCI_LAYOUT_VERSION = "1.0"

# Register 0001, field TEXTO_PADRAO_UTF8. The content is fixed by the layout
# and is used by the SEFAZ validator to certify the file encoding.
FCI_UTF8_STANDARD_TEXT = (
    "Texto em caracteres UTF-8: (dígrafo BR)'ção',"
    "(dígrafo espanhol-enhe)'ñ',(trema)'Ü',(ordinais)'ªº',"
    "(ligamento s+z alemão)'ß'."
)

# The file must be written in UTF-8, other encodings are rejected.
FCI_FILE_ENCODING = "utf-8"

FCI_FILE_LINE_SEPARATOR = "\r\n"

# Maximum number of 5020 (goods) registers allowed in a single file.
FCI_MAX_LINES = 100000

# Registers totalized in the 9900 registers of the block 9, following the
# examples of the manual (only 0000, 0010 and 5020 are totalized).
FCI_TOTALIZED_REGISTERS = ("0000", "0010", "5020")

FCI_STATE = [
    ("draft", "Draft"),
    ("generated", "File Generated"),
    ("transmitted", "Transmitted"),
    ("done", "Done"),
]

# Register 5020, field IN_VALIDACAO_FICHA, filled by the SEFAZ in the
# return file.
FCI_LINE_VALIDATION = [
    ("100", "100 - FCI generated successfully"),
    ("200", "200 - Rejected: the informed NCM does not exist"),
    (
        "300",
        "300 - Accepted: the informed unit of measure does not exist",
    ),
    (
        "400",
        "400 - Rejected: inconsistent amounts and/or import content",
    ),
]

# Table "Abreviaturas e Símbolos" of the manual, used in the register 5020,
# field UNIDADE_MERCADORIA. The code "99" means "other units".
FCI_UOM_CODES = [
    "Ah",
    "ASTM",
    "Bq",
    "°C",
    "CCD",
    "cg",
    "cm",
    "cm2",
    "cm3",
    "cN",
    "cSt",
    "DCI",
    "g",
    "Gbit",
    "GHz",
    "h",
    "HP",
    "HRC",
    "Hz",
    "ISO",
    "IV",
    "kbit",
    "kcal",
    "kg",
    "kgf",
    "kHz",
    "kN",
    "kPa",
    "kV",
    "kVA",
    "kvar",
    "kW",
    "l",
    "m",
    "m-",
    "m2",
    "m3",
    "mbar",
    "Mbit",
    "µCi",
    "mg",
    "MHz",
    "min",
    "mm",
    "mN",
    "MPa",
    "MW",
    "N",
    "n°",
    "nm",
    "Nm",
    "ns",
    "o-",
    "p-",
    "pH",
    "s",
    "t",
    "UV",
    "V",
    "vol",
    "W",
    "x°",
    "%",
    "pç",
    "unid",
    "99",
    "A",
]

# Unit of measure code used when the product unit is not in the table above.
FCI_UOM_CODE_OTHER = "99"
