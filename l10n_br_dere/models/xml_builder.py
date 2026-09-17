# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

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


def _money(value, signed=False):
    amount = float(value or 0.0)
    if abs(amount) < 0.005:
        return "0.00"
    if signed:
        return f"{amount:.2f}"
    return f"{abs(amount):.2f}"


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


def build_d1106(vals, lines=None):
    root, event = _envelope(NS[EVENT_D1106], "evtAplicResTec", vals["id"])
    _ide_evento(event, vals, with_recibo=True)
    _ide_contrib(event, vals["nrInsc"])
    periodo = etree.SubElement(event, "idePeriodo")
    _text(periodo, "perApur", vals["perApur"], required=True)
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
    _ide_evento(event, vals, with_recibo=True)
    _ide_contrib(event, vals["nrInsc"])
    periodo = etree.SubElement(event, "idePeriodo")
    _text(periodo, "perApur", vals["perApur"], required=True)
    info = etree.SubElement(event, "infoDeducoes")
    if not lines:
        raise ValueError("Missing required DeRE field infoDeducao")
    for line in lines:
        node = etree.SubElement(info, "infoDeducao")
        dfe = etree.SubElement(node, "infoDFe")
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
        "protocolo": False,
        "cdResposta": False,
        "descResposta": False,
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
            "protocolo",
            "cdResposta",
            "descResposta",
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
