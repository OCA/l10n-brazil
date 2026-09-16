# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from ..constants import EVENT_D1001, EVENT_D1011, EVENT_D1101, EVENT_D1199, NS


def _money(value):
    return f"{abs(float(value or 0.0)):.2f}"


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


def build_d1001(vals):
    root, event = _envelope(NS[EVENT_D1001], "evtInfoContrib", vals["id"])
    _ide_evento(event, vals)
    _ide_contrib(event, vals["nrInsc"])
    periodo = etree.SubElement(event, "idePeriodo")
    _text(periodo, "iniValid", vals["iniValid"], required=True)
    _text(periodo, "fimValid", vals.get("fimValid"))
    if vals.get("regTribPrinc"):
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
    periodo = etree.SubElement(event, "idePeriodo")
    _text(periodo, "iniValid", vals["iniValid"], required=True)
    _text(periodo, "fimValid", vals.get("fimValid"))
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


def parse_return(xml_content):
    if isinstance(xml_content, bytes):
        payload = xml_content
    else:
        payload = (xml_content or "").encode("utf-8")
    root = etree.fromstring(payload)
    data = {
        "cdRetorno": False,
        "descRetorno": False,
        "nrRecibo": False,
        "protocoloLote": False,
        "tpEv": False,
        "hash": False,
        "ocorrencias": [],
    }
    for element in root.iter():
        name = etree.QName(element).localname
        if name in (
            "cdRetorno",
            "descRetorno",
            "nrRecibo",
            "protocoloLote",
            "tpEv",
            "hash",
        ):
            if element.text:
                data[name] = element.text.strip()
        elif name == "ocorrencias":
            occurrence = {}
            for child in element:
                occurrence[etree.QName(child).localname] = (child.text or "").strip()
            if occurrence:
                data["ocorrencias"].append(occurrence)
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
    return etree.tostring(root, encoding="unicode", pretty_print=True)
