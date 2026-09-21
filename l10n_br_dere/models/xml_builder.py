# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re
from datetime import datetime, timezone
from decimal import ROUND_HALF_EVEN, Decimal

from lxml import etree
from signxml import XMLSigner, methods

from ..constants import (
    EVENT_D1001,
    EVENT_D1011,
    EVENT_D1101,
    EVENT_D1106,
    EVENT_D1121,
    EVENT_D1198,
    EVENT_D1199,
    NS,
)

DS_NS = "http://www.w3.org/2000/09/xmldsig#"
C14N_ALG = "http://www.w3.org/TR/2001/REC-xml-c14n-20010315"


def _round_nbr5891(value, decimals=2):
    quantize = Decimal("1").scaleb(-decimals)
    return Decimal(str(value or 0)).quantize(quantize, rounding=ROUND_HALF_EVEN)


def _money(value, signed=False):
    amount = _round_nbr5891(value)
    if amount.copy_abs() < Decimal("0.005"):
        return "0.00"
    if signed:
        return f"{amount:.2f}"
    return f"{amount.copy_abs():.2f}"


def _text(parent, tag, value, required=False):
    if value in (None, False, ""):
        if required:
            raise ValueError(f"Missing required DeRE field {tag}")
        return None
    node = etree.SubElement(parent, tag)
    node.text = str(value)
    return node


def _envelope(ns, event_tag, event_id):
    root = etree.Element("DeRE", nsmap={None: ns})
    event = etree.SubElement(root, event_tag, id=event_id)
    return root, event


def _ide_evento(parent, vals, with_recibo=False, close=False):
    ide = etree.SubElement(parent, "ideEvento")
    _text(ide, "tpOper", vals["tpOper"], required=True)
    if not close:
        _text(ide, "motExcl", vals.get("motExcl"))
        _text(ide, "nrProc", vals.get("nrProc"))
        if with_recibo:
            _text(ide, "nrRecibo", vals.get("nrRecibo"))
    _text(ide, "tpAmb", vals["tpAmb"], required=True)
    _text(ide, "aplicEmi", vals.get("aplicEmi") or "1", required=True)
    _text(ide, "verAplic", vals["verAplic"], required=True)
    return ide


def _ide_contrib(parent, nr_insc):
    ide = etree.SubElement(parent, "ideContrib")
    _text(ide, "nrInsc", nr_insc, required=True)
    return ide


def _tp_oper(vals):
    return str(vals.get("tpOper") or "1")


def _ide_periodo_tabela(parent, vals):
    periodo = etree.SubElement(parent, "idePeriodo")
    _text(periodo, "iniValid", vals["iniValid"], required=True)
    _text(periodo, "fimValid", vals.get("fimValid"))
    nova = vals.get("novaValidade")
    if _tp_oper(vals) == "2" and nova and nova.get("iniValid"):
        node = etree.SubElement(periodo, "novaValidade")
        _text(node, "iniValid", nova["iniValid"], required=True)
        _text(node, "fimValid", nova.get("fimValid"))
    return periodo


def build_d1001(vals):
    root, event = _envelope(NS[EVENT_D1001], "evtInfoContrib", vals["id"])
    _ide_evento(event, vals)
    _ide_contrib(event, vals["nrInsc"])
    _ide_periodo_tabela(event, vals)
    if _tp_oper(vals) != "3" and vals.get("regTribPrinc"):
        info = etree.SubElement(event, "infoContrib")
        _text(info, "regTribPrinc", vals["regTribPrinc"], required=True)
        for secund in vals.get("regTribSecund") or []:
            _text(info, "regTribSecund", secund)
        _text(info, "indNatTrib", vals.get("indNatTrib") or "0", required=True)
        if vals.get("tpAtividadeFinanc"):
            serv = etree.SubElement(info, "servFinanc")
            acts = etree.SubElement(serv, "tpAtividades")
            for code in vals["tpAtividadeFinanc"]:
                _text(acts, "tpAtividade", code, required=True)
        if vals.get("tpAtividadeSaude"):
            health = etree.SubElement(info, "plAssistSaude")
            acts = etree.SubElement(health, "tpAtividades")
            for code in vals["tpAtividadeSaude"]:
                _text(acts, "tpAtividade", code, required=True)
        if vals.get("tpAtividadeProg"):
            prog = etree.SubElement(info, "prognosticos")
            acts = etree.SubElement(prog, "tpAtividades")
            for code in vals["tpAtividadeProg"]:
                _text(acts, "tpAtividade", code, required=True)
            if vals.get("UFCredenc"):
                ufs = etree.SubElement(prog, "UFsCredenc")
                for uf in vals["UFCredenc"]:
                    _text(ufs, "UFCredenc", uf, required=True)
    return etree.tostring(root, encoding="unicode", pretty_print=True)


def build_d1011(vals, accounts):
    root, event = _envelope(NS[EVENT_D1011], "evtPGCC", vals["id"])
    _ide_evento(event, vals)
    _ide_contrib(event, vals["nrInsc"])
    _ide_periodo_tabela(event, vals)
    if _tp_oper(vals) == "3":
        return etree.tostring(root, encoding="unicode", pretty_print=True)
    info = etree.SubElement(event, "infoPGCC")
    _text(info, "planoCtaRef", vals["planoCtaRef"], required=True)
    _text(info, "freqEncerr", vals["freqEncerr"], required=True)
    contas = etree.SubElement(info, "infoContas")
    for acc in accounts:
        node = etree.SubElement(contas, "infoConta")
        _text(node, "cCta", acc["cCta"], required=True)
        _text(node, "cCtaInterna", acc["cCtaInterna"], required=True)
        _text(node, "cDbrMista", acc["cDbrMista"], required=True)
        _text(node, "nomeCta", acc["nomeCta"], required=True)
        _text(node, "indCta", acc["indCta"], required=True)
        _text(node, "descCta", acc.get("descCta"))
        _text(node, "cCtaSup", acc.get("cCtaSup"))
        _text(node, "cCtaRef", acc["cCtaRef"], required=True)
        _text(node, "nivelCta", acc["nivelCta"], required=True)
        _text(node, "natCta", acc["natCta"], required=True)
        _text(node, "codNat", acc["codNat"], required=True)
        _text(node, "codTrib", acc.get("codTrib"))
        _text(node, "indTribISS", acc.get("indTribISS"))
        _text(node, "idLeiDisp", acc.get("idLeiDisp"))
        _text(node, "iniVig", acc["iniVig"], required=True)
        _text(node, "fimVig", acc.get("fimVig"))
    return etree.tostring(root, encoding="unicode", pretty_print=True)


def build_d1101(vals, lines):
    root, event = _envelope(NS[EVENT_D1101], "evtBalancete", vals["id"])
    _ide_evento(event, vals, with_recibo=True)
    _ide_contrib(event, vals["nrInsc"])
    periodo = etree.SubElement(event, "idePeriodo")
    _text(periodo, "perApur", vals["perApur"], required=True)
    if _tp_oper(vals) == "3":
        return etree.tostring(root, encoding="unicode", pretty_print=True)
    info = etree.SubElement(event, "infoBalancete")
    contas = etree.SubElement(info, "infoContas")
    for line in lines:
        node = etree.SubElement(contas, "infoConta")
        _text(node, "cCta", line["cCta"], required=True)
        _text(node, "natSaldoInic", line["natSaldoInic"], required=True)
        _text(node, "vSaldoInic", _money(line["vSaldoInic"]), required=True)
        _text(node, "vMovDebt", _money(line["vMovDebt"]), required=True)
        if line.get("vAjusteDebt"):
            _text(node, "vAjusteDebt", _money(line["vAjusteDebt"]))
        _text(node, "vMovCred", _money(line["vMovCred"]), required=True)
        if line.get("vAjusteCred"):
            _text(node, "vAjusteCred", _money(line["vAjusteCred"]))
        _text(node, "natSaldoFinal", line["natSaldoFinal"], required=True)
        _text(node, "vSaldoFinal", _money(line["vSaldoFinal"]), required=True)
        if float(line.get("vApur") or 0) > 0:
            _text(node, "natVApur", line["natVApur"], required=True)
        _text(node, "vApur", _money(line.get("vApur") or 0), required=True)
    return etree.tostring(root, encoding="unicode", pretty_print=True)


def build_d1106(vals, lines=None):
    root, event = _envelope(NS[EVENT_D1106], "evtAplicResTec", vals["id"])
    _ide_evento(event, vals, with_recibo=True)
    _ide_contrib(event, vals["nrInsc"])
    periodo = etree.SubElement(event, "idePeriodo")
    _text(periodo, "perApur", vals["perApur"], required=True)
    if _tp_oper(vals) == "3":
        return etree.tostring(root, encoding="unicode", pretty_print=True)
    info = etree.SubElement(event, "infoAplicResTec")
    if vals.get("semAplic"):
        _text(info, "semAplic", vals["semAplic"], required=True)
        return etree.tostring(root, encoding="unicode", pretty_print=True)
    grouped = {}
    for line in lines or []:
        grouped.setdefault(line["cCta"], []).append(line)
    if not grouped:
        raise ValueError("Missing required DeRE field infoAplic")
    for c_cta, assets in grouped.items():
        aplic = etree.SubElement(info, "infoAplic")
        _text(aplic, "cCta", c_cta, required=True)
        for asset in assets:
            det = etree.SubElement(aplic, "detAtivo", idAtivo=asset["idAtivo"])
            _text(det, "descAtivo", asset["descAtivo"], required=True)
            _text(det, "vSaldoInic", _money(asset["vSaldoInic"]), required=True)
            if float(asset.get("vRendPerReceb") or 0):
                _text(det, "vRendPerReceb", _money(asset["vRendPerReceb"]))
            if float(asset.get("vVarMensal") or 0):
                _text(det, "vVarMensal", _money(asset["vVarMensal"], signed=True))
            _text(det, "vPrincLiqResg", _money(asset["vPrincLiqResg"]), required=True)
            if float(asset.get("vRendLiqResg") or 0):
                _text(det, "vRendLiqResg", _money(asset["vRendLiqResg"]))
            _text(det, "vSaldoFinal", _money(asset["vSaldoFinal"]), required=True)
            _text(det, "vApur", _money(asset["vApur"]), required=True)
    return etree.tostring(root, encoding="unicode", pretty_print=True)


def build_d1121(vals, lines):
    root, event = _envelope(NS[EVENT_D1121], "evtRelDeducoes", vals["id"])
    tp_oper = _tp_oper(vals)
    _ide_evento(event, vals, with_recibo=tp_oper in ("2", "3"))
    _ide_contrib(event, vals["nrInsc"])
    periodo = etree.SubElement(event, "idePeriodo")
    _text(periodo, "perApur", vals["perApur"], required=True)
    if tp_oper == "3":
        return etree.tostring(root, encoding="unicode", pretty_print=True)
    if not lines:
        raise ValueError("Missing required DeRE field infoDeducao")
    info = etree.SubElement(event, "infoDeducoes")
    if tp_oper == "4":
        _text(info, "finEvt", vals.get("finEvt"), required=True)
    for line in lines:
        node = etree.SubElement(info, "infoDeducao")
        dfe = etree.SubElement(node, "infoDFe")
        if line.get("chDFeRetif"):
            _text(dfe, "dtEmi", line["dtEmi"], required=True)
            _text(dfe, "chDFeRetif", line["chDFeRetif"], required=True)
            _text(dfe, "tpAtiv", line["tpAtiv"], required=True)
        else:
            _text(dfe, "tpDFe", line["tpDFe"], required=True)
            _text(dfe, "chDFe", line["chDFe"], required=True)
            _text(dfe, "dtEmi", line["dtEmi"], required=True)
            _text(dfe, "tpAtiv", line["tpAtiv"], required=True)
        det = etree.SubElement(node, "detDeducao")
        _text(det, "vOper", _money(line["vOper"]), required=True)
        if line.get("vDedTotal"):
            _text(det, "vDedTotal", _money(line["vDedTotal"]))
        _text(det, "vDed", _money(line["vDed"]), required=True)
        for item in line.get("items") or []:
            item_node = etree.SubElement(node, "itemDFe")
            _text(item_node, "nItem", item["nItem"], required=True)
            _text(item_node, "vItem", _money(item["vItem"]), required=True)
            if item.get("vItemDedTotal"):
                _text(item_node, "vItemDedTotal", _money(item["vItemDedTotal"]))
            _text(item_node, "vItemDed", _money(item["vItemDed"]), required=True)
    return etree.tostring(root, encoding="unicode", pretty_print=True)


def build_d1198(vals):
    root, event = _envelope(NS[EVENT_D1198], "evtReabertMensal", vals["id"])
    _ide_evento(event, vals, close=True)
    _ide_contrib(event, vals["nrInsc"])
    periodo = etree.SubElement(event, "idePeriodo")
    _text(periodo, "perApur", vals["perApur"], required=True)
    info = etree.SubElement(event, "infoReabertura")
    _text(info, "nrReciboReab", vals["nrReciboReab"], required=True)
    return etree.tostring(root, encoding="unicode", pretty_print=True)


def build_d1199(vals):
    root, event = _envelope(NS[EVENT_D1199], "evtFechMensal", vals["id"])
    _ide_evento(event, vals, close=True)
    _ide_contrib(event, vals["nrInsc"])
    periodo = etree.SubElement(event, "idePeriodo")
    _text(periodo, "perApur", vals["perApur"], required=True)
    if vals.get("indInexistDedu"):
        info = etree.SubElement(event, "infoFechamento")
        param = etree.SubElement(info, "infoParamFech")
        _text(param, "indInexistDedu", vals["indInexistDedu"])
    return etree.tostring(root, encoding="unicode", pretty_print=True)


RETURN_HEADER = {
    "ideStatus": ("cdRetorno", "descRetorno"),
    "infoRecEv": (
        "nrRecibo",
        "seqEvento",
        "protocoloLote",
        "protocolo",
        "dhRecepcao",
        "dhProcess",
        "tpEv",
        "hash",
    ),
}
RETURN_FRACTION_RE = re.compile(r"\.(\d+)")
RETURN_TOTAL_FIELDS = (
    "codTrib",
    "indTribISS",
    "vApurTot",
    "vTotSaldoInic",
    "vTotSaldoFinal",
)
# D-9199 groups mapped to the REG_TRIB_SECUND regime codes.
RETURN_TAX_GROUPS = {
    "infoTotFinanceiro": "1",
    "infoTotSaude": "2",
    "infoTotProg": "3",
}
RETURN_DETBC_PATHS = {
    "codBC": ("codBC",),
    "xDetBC": ("xDetBC",),
    "memoriaCalculo": ("memoriaCalculo",),
    "vBCIBS": ("gBCIBS", "vBCIBS"),
    "vBCNIBS": ("gBCIBS", "vBCNIBS"),
    "vDedBCNIBS": ("gBCIBS", "vDedBCN"),
    "vBCApurIBS": ("gBCIBS", "vBCApurIBS"),
    "pIBSMun": ("gBCIBS", "pIBSMun"),
    "vIBSMun": ("gBCIBS", "vIBSMun"),
    "pIBSUF": ("gBCIBS", "pIBSUF"),
    "vIBSUF": ("gBCIBS", "vIBSUF"),
    "pIBS": ("gBCIBS", "pIBS"),
    "vIBSTot": ("gBCIBS", "vIBSTot"),
    "vBCCBS": ("gBCCBS", "vBCCBS"),
    "vBCNCBS": ("gBCCBS", "vBCNCBS"),
    "vDedBCNCBS": ("gBCCBS", "vDedBCN"),
    "vBCApurCBS": ("gBCCBS", "vBCApurCBS"),
    "pCBS": ("gBCCBS", "pCBS"),
    "vCBS": ("gBCCBS", "vCBS"),
    "vBCIS": ("gBCIS", "vBCIS"),
    "vBCApurIS": ("gBCIS", "vBCApurIS"),
    "pIS": ("gBCIS", "pIS"),
    "vIS": ("gBCIS", "vIS"),
    "vSaldoFinalBCNIBS": ("infoBCN", "gBCNIBS", "vSaldoFinal"),
    "vSaldoFinalBCNCBS": ("infoBCN", "gBCNCBS", "vSaldoFinal"),
}
RETURN_TAX_TOTALS = ("vIS", "vIBSMun", "vIBSUF", "vIBSTot", "vCBS")
RETURN_VALIDITY_FIELDS = (
    "nrRecibo",
    "iniValid",
    "fimValid",
    "fimValidEfetiva",
    "indAjusteAuto",
)
RETURN_GAP_FIELDS = ("iniLacuna", "fimLacuna")


def _localname(element):
    return etree.QName(element).localname


def _child(element, name):
    if element is None:
        return None
    for child in element.iterchildren(tag=etree.Element):
        if _localname(child) == name:
            return child
    return None


def _path(element, *names):
    for name in names:
        element = _child(element, name)
        if element is None:
            return None
    return element


def _path_text(element, *names):
    element = _path(element, *names)
    if element is None or not element.text:
        return False
    return element.text.strip()


def parse_datetime(value):
    """Return a naive UTC datetime from a DeRE xs:dateTime string."""
    if not value:
        return False
    text = value.strip().replace("Z", "+00:00")
    text = RETURN_FRACTION_RE.sub(
        lambda match: "." + (match.group(1) + "000000")[:6], text, count=1
    )
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        return False
    if moment.tzinfo:
        moment = moment.astimezone(timezone.utc).replace(tzinfo=None)
    return moment


def _children(element, name):
    if element is None:
        return []
    return [
        child
        for child in element.iterchildren(tag=etree.Element)
        if _localname(child) == name
    ]


def _return_totals(node):
    info = _child(node, "infoEvento")
    balan = _child(info, "infoTotBalan")
    if balan is not None:
        return [
            {name: _path_text(group, name) for name in RETURN_TOTAL_FIELDS}
            for group in _children(balan, "gTotalCodTrib")
        ]
    total = _path_text(info, "infoTotAplicFin", "vApurTot")
    return [{"vApurTot": total}] if total else []


def _return_taxes(node):
    info = _child(node, "infoEvento")
    lines = []
    for group, regime in RETURN_TAX_GROUPS.items():
        for det in _children(_child(info, group), "detBC"):
            vals = {
                key: _path_text(det, *path) for key, path in RETURN_DETBC_PATHS.items()
            }
            vals["regime"] = regime
            lines.append(vals)
    general = _child(info, "totalTributosGeral")
    total = {}
    if general is not None:
        total = {name: _path_text(general, name) for name in RETURN_TAX_TOTALS}
    return {"lines": lines, "total": total}


def _return_receipts(node):
    info_adic = _path(node, "infoEvento", "infoAdic")
    return {
        "nrReciboBalancete": _path_text(info_adic, "nrReciboBalancete"),
        "nrReciboAplicFin": _path_text(info_adic, "nrReciboAplicFin"),
        "nrReciboRelDedu": [
            element.text.strip()
            for element in _children(info_adic, "nrReciboRelDedu")
            if element.text
        ],
    }


def _return_extract(node):
    """Return the D-9001 validity photo, or {} when the group is absent.

    An empty ``extratoEventos`` still yields empty lists, because it means
    the RFB has no validity in force for that table.
    """
    extract = _child(node, "extratoEventos")
    if extract is None:
        return {}
    return {
        "validity": [
            {name: _path_text(det, name) for name in RETURN_VALIDITY_FIELDS}
            for det in _children(extract, "detEvento")
        ],
        "gaps": [
            {name: _path_text(det, name) for name in RETURN_GAP_FIELDS}
            for det in _children(extract, "detLacuna")
        ],
    }


def _return_node(root):
    if _localname(root).startswith("evtRetorno"):
        return root
    if _localname(root) == "DeRE":
        for child in root.iterchildren(tag=etree.Element):
            if _localname(child).startswith("evtRetorno"):
                return child
    return None


def _occurrence_vals(element):
    occurrence = {}
    for child in element:
        occurrence[_localname(child)] = (child.text or "").strip()
    return occurrence


def _read_return_header(node, data):
    # D-9001 repeats nrRecibo inside extratoEventos, so the header must be
    # read from its own groups only.
    for group, names in RETURN_HEADER.items():
        parent = _child(node, group)
        source = parent if parent is not None else node
        for name in names:
            element = _child(source, name)
            if element is not None and element.text:
                data[name] = element.text.strip()
    return data


def _parse_event_return(root):
    data = {
        "id": False,
        "cdRetorno": False,
        "descRetorno": False,
        "nrRecibo": False,
        "protocoloLote": False,
        "protocolo": False,
        "tpEv": False,
        "hash": False,
        "seqEvento": False,
        "dhRecepcao": False,
        "dhProcess": False,
        "returnTag": False,
        "xml": False,
        "perApur": False,
        "nrReciboPGCC": False,
        "totals": [],
        "taxes": {"lines": [], "total": {}},
        "receipts": {},
        "extract": {},
        "ocorrencias": [],
    }
    node = _return_node(root)
    if node is not None:
        data.update(
            {
                "returnTag": _localname(node),
                "xml": etree.tostring(root, encoding="unicode"),
                "perApur": _path_text(node, "infoEvento", "idePeriodo", "perApur"),
                "nrReciboPGCC": _path_text(
                    node, "infoEvento", "infoAdic", "nrReciboPGCC"
                ),
                "totals": _return_totals(node),
                "taxes": _return_taxes(node),
                "receipts": _return_receipts(node),
                "extract": _return_extract(node),
            }
        )
        _read_return_header(node, data)
        root = node
    if root.get("id"):
        data["id"] = root.get("id")
    for element in root.iter():
        name = _localname(element)
        if name in (
            "cdRetorno",
            "descRetorno",
            "nrRecibo",
            "protocoloLote",
            "protocolo",
            "tpEv",
            "hash",
        ):
            if node is None and element.text:
                data[name] = element.text.strip()
        elif name == "ocorrencias":
            occurrence = _occurrence_vals(element)
            if occurrence and "codigo" in occurrence:
                data["ocorrencias"].append(occurrence)
        elif name == "ocorrencia":
            occurrence = _occurrence_vals(element)
            if occurrence:
                data["ocorrencias"].append(occurrence)
    return data


def parse_return(xml_content):
    if isinstance(xml_content, bytes):
        payload = xml_content
    else:
        payload = (xml_content or "").encode("utf-8")
    root = etree.fromstring(payload)
    event = _parse_event_return(root)
    data = dict(event, cdResposta=False, descResposta=False, events=[])
    for element in root.iter():
        name = _localname(element)
        if name in ("cdResposta", "descResposta") and element.text:
            data[name] = element.text.strip()
        elif name == "evento" and element.getparent() is not None:
            parent = _localname(element.getparent())
            if parent == "retornoEventos":
                inner = next(iter(element), None)
                parsed = _parse_event_return(inner if inner is not None else element)
                parsed["id"] = element.get("id") or parsed.get("id")
                data["events"].append(parsed)
    if not data["events"] and data.get("cdRetorno"):
        data["events"] = [event]
    return data


def build_lote(nr_insc, events):
    ns = NS["lote"]
    root = etree.Element("DeRE", nsmap={None: ns})
    lote = etree.SubElement(root, "loteEventos")
    ide = etree.SubElement(lote, "ideContrib")
    _text(ide, "nrInsc", nr_insc, required=True)
    eventos = etree.SubElement(lote, "eventos")
    for event in events:
        node = etree.SubElement(eventos, "evento", id=event["id"])
        inner = etree.fromstring(event["xml"].encode("utf-8"))
        node.append(inner)
    return etree.tostring(root, encoding="unicode")


def sign_event(xml_content, certificado, reference):
    if isinstance(xml_content, bytes):
        payload = xml_content
    else:
        payload = (xml_content or "").encode("utf-8")
    root = etree.fromstring(payload)
    for element in root.iter("*"):
        if element.text is not None and not element.text.strip():
            element.text = None
        if element.tail is not None and not element.tail.strip():
            element.tail = None
    signer = XMLSigner(
        method=methods.enveloped,
        signature_algorithm="rsa-sha256",
        digest_algorithm="sha256",
        c14n_algorithm=C14N_ALG,
    )
    signer.excise_empty_xmlns_declarations = True
    cert_pem = certificado.cert_chave()[0]
    signed_root = signer.sign(
        root,
        key=certificado.key,
        cert=cert_pem,
        reference_uri=f"#{reference}",
        id_attribute="id",
    )
    event_node = signed_root.find(f".//*[@id='{reference}']")
    signature = signed_root.find(f".//{{{DS_NS}}}Signature")
    if event_node is not None and signature is not None:
        parent = event_node.getparent()
        if parent is not None and signature.getparent() is not parent:
            parent.append(signature)
    return etree.tostring(signed_root, encoding="unicode")
