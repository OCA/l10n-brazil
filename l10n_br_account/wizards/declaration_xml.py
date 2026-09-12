# Copyright 2026 KMEE (Ygor Carvalho <ygor.carvalho@kmee.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
"""Reader of the import declaration XML that the Siscomex hands out.

Kept free of Odoo on purpose: the shape of the file is the whole difficulty
here, and a plain function over bytes can be exercised without a database.

Every number in the file is an integer with the decimals implied, and the
implied place changes by field: money and rates carry two, quantity carries
five, unit value carries seven. Reading a value with the wrong scale gives a
number that looks plausible and is off by a factor of ten, so the scale lives
next to each field instead of being guessed at the call site.
"""

from datetime import date
from xml.etree import ElementTree

MONEY = 2
RATE = 2
QUANTITY = 5
UNIT_VALUE = 7
WEIGHT = 5


class DeclarationXmlError(ValueError):
    """The file is not an import declaration this reader understands."""


def _number(element, scale):
    if element is None or not (element.text or "").strip():
        return 0.0
    return int(element.text) / (10**scale)


def _text(parent, tag):
    element = parent.find(tag)
    return (element.text or "").strip() if element is not None else ""


def _amount(parent, tag, scale=MONEY):
    return _number(parent.find(tag), scale)


def _date(parent, tag):
    raw = _text(parent, tag)
    if len(raw) != 8 or not raw.isdigit():
        return False
    return date(int(raw[:4]), int(raw[4:6]), int(raw[6:8]))


def _ncm(raw):
    """The file writes the NCM without the dots the catalog uses."""
    digits = "".join(c for c in raw if c.isdigit())
    if len(digits) != 8:
        return raw
    return f"{digits[:4]}.{digits[4:6]}.{digits[6:]}"


def _description(raw):
    """The description of the item, without the tail the Siscomex glues to it.

    The classification code travels inside the description as `cClassTrib=[...]`,
    and the field comes padded with spaces and carriage returns.
    """
    text = raw.replace("\r", " ")
    marker = text.find("cClassTrib=")
    if marker >= 0:
        text = text[:marker]
    return " ".join(text.split())


def _items(addition):
    items = []
    for item in addition.findall("mercadoria"):
        items.append(
            {
                "sequence": _text(item, "numeroSequencialItem"),
                "description": _description(_text(item, "descricaoMercadoria")),
                "quantity": _amount(item, "quantidade", QUANTITY),
                "unit_value": _amount(item, "valorUnitario", UNIT_VALUE),
                "uom": _text(item, "unidadeMedida").strip(),
            }
        )
    return items


def _additions(declaration):
    additions = []
    for addition in declaration.findall("adicao"):
        additions.append(
            {
                "number": _text(addition, "numeroAdicao"),
                "ncm": _ncm(_text(addition, "dadosMercadoriaCodigoNcm")),
                # The base of the Import Tax is the customs value of the
                # addition: the goods plus the freight and the insurance that
                # the file already spread over the additions.
                "customs_value": _amount(addition, "iiBaseCalculo"),
                "goods_value": _amount(addition, "condicaoVendaValorReais"),
                "ii_rate": _amount(addition, "iiAliquotaAdValorem", RATE),
                "ii_value": _amount(addition, "iiAliquotaValorRecolher"),
                "ipi_rate": _amount(addition, "ipiAliquotaAdValorem", RATE),
                "ipi_value": _amount(addition, "ipiAliquotaValorRecolher"),
                "pis_rate": _amount(addition, "pisPasepAliquotaAdValorem", RATE),
                "pis_value": _amount(addition, "pisPasepAliquotaValorRecolher"),
                "cofins_value": _amount(addition, "cofinsAliquotaValorRecolher"),
                "net_weight": _amount(addition, "dadosMercadoriaPesoLiquido", WEIGHT),
                "exporter": _text(addition, "fornecedorNome"),
                "manufacturer": _text(addition, "fabricanteNome"),
                "origin_country": _text(addition, "paisOrigemMercadoriaNome"),
                "items": _items(addition),
            }
        )
    return additions


def parse_declaration(content):
    """Turn the XML of one import declaration into plain data.

    Returns the header of the declaration and its additions, each with its own
    NCM, its own rates and the goods it covers. The additions are the point:
    the tax the declaration charged changes from one to the next, and a single
    total spread by weight over the whole note cannot reproduce it.
    """
    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError as error:
        raise DeclarationXmlError(f"The file is not valid XML: {error}") from error

    declaration = root if root.tag == "declaracaoImportacao" else None
    if declaration is None:
        declaration = root.find("declaracaoImportacao")
    if declaration is None:
        raise DeclarationXmlError(
            "No declaracaoImportacao in the file. The expected one is the XML "
            "the Siscomex hands out for the import declaration."
        )

    icms = declaration.find("icms")
    return {
        "number": _text(declaration, "numeroDI"),
        "registration_date": _date(declaration, "dataRegistro"),
        "clearance_date": _date(declaration, "dataDesembaraco"),
        "transport_via": _text(declaration, "viaTransporteCodigo").lstrip("0"),
        "clearance_place": _text(declaration, "armazenamentoRecintoAduaneiroNome")
        or _text(declaration, "cargaUrfEntradaNome"),
        "clearance_state": _text(icms, "ufIcms") if icms is not None else "",
        "importer_document": _text(declaration, "importadorNumero"),
        "freight": _amount(declaration, "freteTotalReais"),
        "insurance": _amount(declaration, "seguroTotalReais"),
        "icms_value": _amount(icms, "valorTotalIcms") if icms is not None else 0.0,
        "gross_weight": _amount(declaration, "cargaPesoBruto", WEIGHT),
        "net_weight": _amount(declaration, "cargaPesoLiquido", WEIGHT),
        "additions": _additions(declaration),
    }
