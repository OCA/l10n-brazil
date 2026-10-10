# Copyright 2026 Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import gzip
import re
import zlib
from datetime import datetime, timezone

from lxml import etree

from ..constants.nfse_dfe import (
    NFSE_ACCESS_KEY_SIZE,
    NFSE_CANCEL_EVENT_CODES,
    NFSE_CANCEL_EVENT_NAMES,
    NFSE_EVENT_CODE_BY_NAME,
)


class NfseNacionalBinding:
    """Plain view of a national NFS-e XML, used by the import wizard.

    ``l10n_br_nfse_spec`` exposes Odoo mixins, not an xsdata binding, so the
    wizard detects this object before the generic XML parser runs.
    """

    is_national_nfse = True

    def __init__(self, values):
        self.access_key = values.get("access_key")
        self.number = values.get("number")
        self.serie = values.get("serie")
        self.emission_date = values.get("emission_date")
        self.provider_cnpj = values.get("provider_cnpj")
        self.provider_name = values.get("provider_name")
        self.provider = values.get("provider") or {}
        self.service_value = values.get("service_value") or 0.0
        self.description = values.get("description")
        self.issqn_base = values.get("issqn_base") or 0.0
        self.issqn_percent = values.get("issqn_percent") or 0.0
        self.issqn_value = values.get("issqn_value") or 0.0
        self.issqn_wh_percent = values.get("issqn_wh_percent") or 0.0
        self.issqn_wh_value = values.get("issqn_wh_value") or 0.0
        self.service_lc116_code = values.get("service_lc116_code")
        self.service_nbs_code = values.get("service_nbs_code")
        self.issqn_city_ibge = values.get("issqn_city_ibge")
        self.rps_number = values.get("rps_number")
        self.ibs_base = values.get("ibs_base") or 0.0
        self.ibs_percent = values.get("ibs_percent") or 0.0
        self.ibs_reduction = values.get("ibs_reduction") or 0.0
        self.ibs_value = values.get("ibs_value") or 0.0
        self.cbs_base = values.get("cbs_base") or 0.0
        self.cbs_percent = values.get("cbs_percent") or 0.0
        self.cbs_reduction = values.get("cbs_reduction") or 0.0
        self.cbs_value = values.get("cbs_value") or 0.0
        self.ibs_cbs_cst = values.get("ibs_cbs_cst")
        self.tax_classification_code = values.get("tax_classification_code")
        self.pis_cofins_cst = values.get("pis_cofins_cst")
        self.pis_cofins_base = values.get("pis_cofins_base") or 0.0
        self.pis_percent = values.get("pis_percent") or 0.0
        self.pis_value = values.get("pis_value") or 0.0
        self.cofins_percent = values.get("cofins_percent") or 0.0
        self.cofins_value = values.get("cofins_value") or 0.0
        self.pis_withheld = bool(values.get("pis_withheld"))
        self.cofins_withheld = bool(values.get("cofins_withheld"))
        self.irpj_wh_value = values.get("irpj_wh_value") or 0.0
        self.csll_wh_value = values.get("csll_wh_value") or 0.0


def decode_arquivo_xml(value):
    """Return XML bytes from an ADN ``ArquivoXml`` or a wizard binary."""
    if not value:
        return None
    if isinstance(value, bytes):
        if value[:1] in (b"<", b"\x1f"):
            raw = value
        else:
            try:
                raw = base64.b64decode(value)
            except (ValueError, TypeError):
                raw = value
    else:
        text = str(value).strip()
        if text.startswith("<"):
            return text.encode("utf-8")
        try:
            raw = base64.b64decode(text)
        except (ValueError, TypeError):
            return None
    if raw[:2] == b"\x1f\x8b":
        try:
            raw = gzip.decompress(raw)
        except (OSError, EOFError, zlib.error):
            return None
    return raw


def normalize_access_key(value):
    """Return a 50-digit NFS-e access key, or False."""
    digits = re.sub(r"\D", "", value or "")
    if len(digits) == NFSE_ACCESS_KEY_SIZE:
        return digits
    if len(digits) > NFSE_ACCESS_KEY_SIZE:
        tail = digits[-NFSE_ACCESS_KEY_SIZE:]
        if len(tail) == NFSE_ACCESS_KEY_SIZE:
            return tail
    return False


def parse_nfse_datetime(value):
    """Parse an NFS-e date-time into a naive UTC datetime."""
    if not value:
        return False
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return False
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def _local_name(tag):
    if not tag:
        return ""
    return tag.split("}", 1)[-1]


def _is_nfse_document(root):
    if _local_name(root.tag) == "NFSe":
        return True
    return bool(root.xpath("./*[local-name()='infNFSe']"))


def _text(root, *paths):
    for path in paths:
        found = root.xpath(path)
        if found and found[0].text and found[0].text.strip():
            return found[0].text.strip()
    return None


def _amount(value):
    if not value:
        return 0.0
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return 0.0


def _digits(value):
    return re.sub(r"\D", "", value or "")


# tpRetPisCofins (NT 007). CSLL and IRRF use their own vRet* tags.
_PIS_RETAINED = {"1", "3", "4", "5", "9"}
_COFINS_RETAINED = {"1", "3", "4", "6", "7"}


def _step(node, name):
    if node is None:
        return None
    found = node.xpath(f"./*[local-name()='{name}']")
    return found[0] if found else None


def _path(node, *names):
    current = node
    for name in names:
        current = _step(current, name)
        if current is None:
            return None
    return current


def _path_text(node, *names):
    current = _path(node, *names)
    if current is None or not current.text or not current.text.strip():
        return None
    return current.text.strip()


def _inf_nfse(root):
    if _local_name(root.tag) == "infNFSe":
        return root
    found = _step(root, "infNFSe")
    if found is not None:
        return found
    return _path(root, "NFSe", "infNFSe")


def _ibs_cbs_values(inf_nfse, inf_dps):
    """Read IBS/CBS totals and the DPS classification.

    Amounts live under ``infNFSe/IBSCBS``. CST and cClassTrib live under
    ``infDPS/IBSCBS``. The fiscal line has one IBS rate, so the UF nominal
    rate is kept and the value is the IBS total (UF + municipal).
    """
    base = _amount(_path_text(inf_nfse, "IBSCBS", "valores", "vBC"))
    ibs_value = _amount(_path_text(inf_nfse, "IBSCBS", "totCIBS", "gIBS", "vIBSTot"))
    if not ibs_value:
        ibs_value = _amount(
            _path_text(inf_nfse, "IBSCBS", "totCIBS", "gIBS", "gIBSUFTot", "vIBSUF")
        ) + _amount(
            _path_text(inf_nfse, "IBSCBS", "totCIBS", "gIBS", "gIBSMunTot", "vIBSMun")
        )
    return {
        "ibs_base": base,
        "ibs_percent": _amount(
            _path_text(inf_nfse, "IBSCBS", "valores", "uf", "pIBSUF")
        ),
        "ibs_reduction": _amount(
            _path_text(inf_nfse, "IBSCBS", "valores", "uf", "pRedAliqUF")
        ),
        "ibs_value": ibs_value,
        "cbs_base": base,
        "cbs_percent": _amount(
            _path_text(inf_nfse, "IBSCBS", "valores", "fed", "pCBS")
        ),
        "cbs_reduction": _amount(
            _path_text(inf_nfse, "IBSCBS", "valores", "fed", "pRedAliqCBS")
        ),
        "cbs_value": _amount(_path_text(inf_nfse, "IBSCBS", "totCIBS", "gCBS", "vCBS")),
        "ibs_cbs_cst": _path_text(
            inf_dps, "IBSCBS", "valores", "trib", "gIBSCBS", "CST"
        ),
        "tax_classification_code": _path_text(
            inf_dps, "IBSCBS", "valores", "trib", "gIBSCBS", "cClassTrib"
        ),
    }


def _federal_tax_values(inf_dps):
    """Read PIS/COFINS and the federal withholdings from the DPS."""
    pis_cofins = _path(inf_dps, "valores", "trib", "tribFed", "piscofins")
    retention = _path_text(pis_cofins, "tpRetPisCofins") or ""
    federal = _path(inf_dps, "valores", "trib", "tribFed")
    return {
        "pis_cofins_cst": _path_text(pis_cofins, "CST"),
        "pis_cofins_base": _amount(_path_text(pis_cofins, "vBCPisCofins")),
        "pis_percent": _amount(_path_text(pis_cofins, "pAliqPis")),
        "pis_value": _amount(_path_text(pis_cofins, "vPis")),
        "cofins_percent": _amount(_path_text(pis_cofins, "pAliqCofins")),
        "cofins_value": _amount(_path_text(pis_cofins, "vCofins")),
        "pis_withheld": retention in _PIS_RETAINED,
        "cofins_withheld": retention in _COFINS_RETAINED,
        "irpj_wh_value": _amount(_path_text(federal, "vRetIRRF")),
        "csll_wh_value": _amount(_path_text(federal, "vRetCSLL")),
    }


def _party_address(node):
    """Read a national address (``end`` or the emitter ``enderNac``)."""
    if node is None:
        return {}
    national = _step(node, "endNac")
    if national is None:
        national = node
    return {
        "street_name": _path_text(node, "xLgr"),
        "street_number": _path_text(node, "nro"),
        "street2": _path_text(node, "xCpl"),
        "district": _path_text(node, "xBairro"),
        "zip": _digits(_path_text(national, "CEP")),
        "city_ibge": _digits(_path_text(national, "cMun")),
    }


def _party(node):
    if node is None:
        return {}
    values = {
        "cnpj": _digits(_path_text(node, "CNPJ")),
        "cpf": _digits(_path_text(node, "CPF")),
        "legal_name": _path_text(node, "xNome"),
        "name": _path_text(node, "xFant") or _path_text(node, "xNome"),
        "im": _path_text(node, "IM"),
        "phone": _path_text(node, "fone"),
        "email": _path_text(node, "email"),
    }
    address = _step(node, "end")
    if address is None:
        address = _step(node, "enderNac")
    values.update(_party_address(address))
    return {key: value for key, value in values.items() if value}


def _provider_party(inf_nfse, inf_dps):
    """Provider from ``infDPS/prest``. Emitter data fills gaps only.

    ``tpEmit`` can be the taker, so ``infNFSe/emit`` is used only when its
    CNPJ is the same as the provider.
    """
    provider = _party(_path(inf_dps, "prest"))
    emitter = _party(_step(inf_nfse, "emit"))
    same_company = (
        emitter.get("cnpj") and emitter.get("cnpj") == provider.get("cnpj")
    ) or (emitter.get("cpf") and emitter.get("cpf") == provider.get("cpf"))
    if same_company:
        for key, value in emitter.items():
            provider.setdefault(key, value)
    return provider


def _access_key_from_root(root):
    nodes = root.xpath("./*[local-name()='infNFSe']")
    if not nodes:
        nodes = root.xpath(".//*[local-name()='infNFSe']")
    if nodes:
        return normalize_access_key(nodes[0].get("Id"))
    return False


def parse_nfse_xml(xml_bytes):
    """Map a national NFS-e XML to a dict. Returns None for other documents."""
    if not xml_bytes:
        return None
    try:
        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError:
        return None
    if not _is_nfse_document(root):
        return None
    inf_nfse = _inf_nfse(root)
    inf_dps = _path(inf_nfse, "DPS", "infDPS")
    provider = _provider_party(inf_nfse, inf_dps)
    provider_cnpj = provider.get("cnpj") or provider.get("cpf") or ""
    provider_name = provider.get("legal_name") or provider.get("name")
    service_value = _amount(
        _text(
            root,
            ".//*[local-name()='vServPrest']/*[local-name()='vServ']",
            "./*[local-name()='infNFSe']/*[local-name()='valores']"
            "/*[local-name()='vLiq']",
        )
    )
    issqn_base = _amount(
        _text(
            root,
            "./*[local-name()='infNFSe']/*[local-name()='valores']/*[local-name()='vBC']",
        )
    )
    issqn_percent = _amount(
        _text(
            root,
            "./*[local-name()='infNFSe']/*[local-name()='valores']"
            "/*[local-name()='pAliqAplic']",
        )
    )
    issqn_value = _amount(
        _text(
            root,
            "./*[local-name()='infNFSe']/*[local-name()='valores']"
            "/*[local-name()='vISSQN']",
        )
    )
    retention = _text(
        root,
        ".//*[local-name()='tribMun']/*[local-name()='tpRetISSQN']",
    )
    withheld = retention in {"2", "3"}
    emission = parse_nfse_datetime(
        _text(
            root,
            ".//*[local-name()='infDPS']/*[local-name()='dhEmi']",
            "./*[local-name()='infNFSe']/*[local-name()='dhProc']",
        )
    )
    return {
        "access_key": _access_key_from_root(root),
        "number": _text(root, "./*[local-name()='infNFSe']/*[local-name()='nNFSe']"),
        "serie": _text(root, ".//*[local-name()='infDPS']/*[local-name()='serie']"),
        "emission_date": emission,
        "provider_cnpj": provider_cnpj or False,
        "provider_name": provider_name,
        "provider": provider,
        "service_value": service_value,
        "description": _text(
            root,
            ".//*[local-name()='cServ']/*[local-name()='xDescServ']",
        ),
        "issqn_base": issqn_base,
        "issqn_percent": issqn_percent,
        "issqn_value": issqn_value,
        "issqn_wh_percent": issqn_percent if withheld else 0.0,
        "issqn_wh_value": issqn_value if withheld else 0.0,
        "service_lc116_code": _text(
            root,
            ".//*[local-name()='cServ']/*[local-name()='cTribNac']",
        ),
        "service_nbs_code": _digits(
            _text(root, ".//*[local-name()='cServ']/*[local-name()='cNBS']")
        ),
        "issqn_city_ibge": _digits(
            _text(root, "./*[local-name()='infNFSe']/*[local-name()='cLocIncid']")
        ),
        "rps_number": _text(root, ".//*[local-name()='infDPS']/*[local-name()='nDPS']"),
        **_ibs_cbs_values(inf_nfse, inf_dps),
        **_federal_tax_values(inf_dps),
    }


def parse_nfse_file(file_data):
    """Parse a base64 wizard file when it is a national NFS-e."""
    xml_bytes = decode_arquivo_xml(file_data)
    values = parse_nfse_xml(xml_bytes)
    if not values:
        return None
    return NfseNacionalBinding(values)


def normalize_event_code(code):
    """Return the 6-digit national event code, or False."""
    if not code:
        return False
    text = str(code).strip()
    mapped = NFSE_EVENT_CODE_BY_NAME.get(text.upper())
    if mapped:
        return mapped
    if text[:1] in {"e", "E"} and text[1:].isdigit():
        text = text[1:]
    if text.isdigit() and len(text) == 6:
        return text
    return False


def is_cancel_event(code):
    """True only for a cancellation that was actually registered."""
    if not code:
        return False
    if str(code).strip().upper() in NFSE_CANCEL_EVENT_NAMES:
        return True
    return normalize_event_code(code) in NFSE_CANCEL_EVENT_CODES


def _event_code_from_root(root):
    """The national event has no ``tpEvento`` tag.

    The code is the ``eNNNNNN`` child of ``infPedReg``, and it is also the
    6 digits before the sequence in ``infPedReg/@Id``.
    """
    for node in root.xpath(".//*[local-name()='infPedReg']"):
        for child in node:
            name = _local_name(child.tag)
            if re.fullmatch(r"[eE]\d{6}", name):
                return name[1:]
        digits = re.sub(r"\D", "", node.get("Id") or "")
        if len(digits) >= 9:
            return digits[-9:-3]
    return False


def parse_nfse_event_xml(xml_bytes):
    """Map a national NFS-e event XML to a dict, or None."""
    if not xml_bytes:
        return None
    try:
        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError:
        return None
    event_type = _event_code_from_root(root) or _text(
        root,
        ".//*[local-name()='infEvento']/*[local-name()='tpEvento']",
        ".//*[local-name()='infPedReg']/*[local-name()='tpEvento']",
    )
    access_key = normalize_access_key(
        _text(
            root,
            ".//*[local-name()='infPedReg']/*[local-name()='chNFSe']",
            ".//*[local-name()='infEvento']/*[local-name()='chNFSe']",
        )
    )
    if not event_type and not access_key and _local_name(root.tag) != "evento":
        return None
    return {
        "access_key": access_key,
        "event_type": normalize_event_code(event_type) or event_type,
        "is_cancel": is_cancel_event(event_type),
    }


def xml_root_is_nfse(xml_bytes):
    if not xml_bytes:
        return False
    try:
        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError:
        return False
    return _is_nfse_document(root)
