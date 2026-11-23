# Copyright 2026 Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re
from datetime import datetime, timezone
from enum import Enum

from lxml import etree
from nfelib.nfse.bindings.v1_0.nfse_v1_01 import Nfse
from xsdata.exceptions import ParserError
from xsdata.formats.dataclass.parsers.config import ParserConfig

from ..constants.nfse import NFSE_ACCESS_KEY_SIZE


class NfseNacionalBinding:
    """Plain view of a national NFS-e, used by the import wizard.

    The authorized note is read with the nfelib 1.01 binding. The wizard
    receives this flat object, not the xsdata tree.
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
        self.taker = values.get("taker") or {}
        self.tax_nature = values.get("tax_nature")
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


_NFSE_PARSER_CONFIG = ParserConfig(fail_on_unknown_properties=False)


def _node(parent, name):
    if parent is None:
        return None
    return getattr(parent, name, None)


def _walk(parent, *names):
    current = parent
    for name in names:
        current = _node(current, name)
    return current


def _xsd_text(value):
    """Return the XML text of a binding value, unwrapping xsdata enums."""
    if value is None:
        return None
    if isinstance(value, Enum):
        value = value.value
    text = str(value).strip()
    return text or None


def _node_text(parent, *names):
    return _xsd_text(_walk(parent, *names))


def _legacy_ibs_cbs_classification(xml_bytes):
    """CST and cClassTrib of a DPS in the pre-NT 009 layout.

    nfelib 3.3.0 only models the NT 009 position, so the tags nested in
    ``trib/gIBSCBS`` of an older note are dropped by the binding and have to
    be read from the XML.
    """
    if not xml_bytes:
        return None, None
    try:
        root = etree.fromstring(
            xml_bytes.encode() if isinstance(xml_bytes, str) else xml_bytes
        )
    except etree.XMLSyntaxError:
        return None, None
    group = (
        ".//*[local-name()='infDPS']/*[local-name()='IBSCBS']"
        "/*[local-name()='valores']/*[local-name()='trib']"
        "/*[local-name()='gIBSCBS']"
    )
    return (
        _text(root, group + "/*[local-name()='CST']"),
        _text(root, group + "/*[local-name()='cClassTrib']"),
    )


def _ibs_cbs_classification(inf_dps, xml_bytes=None):
    """Return the ``(CST, cClassTrib)`` pair of the DPS.

    NT 009 (leiaute 1.04.01) moved both tags directly under
    ``infDPS/IBSCBS/valores/trib``. Notes issued with the previous layout keep
    them inside ``trib/gIBSCBS``, so read the newer position first and fall
    back to the old one.
    """
    trib = _walk(inf_dps, "IBSCBS", "valores", "trib")
    for node in (trib, _node(trib, "gIBSCBS")):
        cst = _node_text(node, "CST")
        classification = _node_text(node, "cClassTrib")
        if cst or classification:
            return cst, classification
    return _legacy_ibs_cbs_classification(xml_bytes)


def _ibs_cbs_values(inf_nfse, inf_dps, xml_bytes=None):
    """Read IBS/CBS totals and the DPS classification.

    Amounts live under ``infNFSe/IBSCBS``. CST and cClassTrib live under
    ``infDPS/IBSCBS/valores/trib`` (NT 009), or under its ``gIBSCBS`` group on
    notes of the previous layout. The fiscal line has one IBS rate, so the UF
    nominal rate is kept and the value is the IBS total (UF + municipal).
    """
    ibscbs = _node(inf_nfse, "IBSCBS")
    base = _amount(_node_text(ibscbs, "valores", "vBC"))
    ibs_value = _amount(_node_text(ibscbs, "totCIBS", "gIBS", "vIBSTot"))
    if not ibs_value:
        ibs_value = _amount(
            _node_text(ibscbs, "totCIBS", "gIBS", "gIBSUFTot", "vIBSUF")
        ) + _amount(_node_text(ibscbs, "totCIBS", "gIBS", "gIBSMunTot", "vIBSMun"))
    ibs_cbs_cst, tax_classification_code = _ibs_cbs_classification(inf_dps, xml_bytes)
    return {
        "ibs_base": base,
        "ibs_percent": _amount(_node_text(ibscbs, "valores", "uf", "pIBSUF")),
        "ibs_reduction": _amount(_node_text(ibscbs, "valores", "uf", "pRedAliqUF")),
        "ibs_value": ibs_value,
        "cbs_base": base,
        "cbs_percent": _amount(_node_text(ibscbs, "valores", "fed", "pCBS")),
        "cbs_reduction": _amount(_node_text(ibscbs, "valores", "fed", "pRedAliqCBS")),
        "cbs_value": _amount(_node_text(ibscbs, "totCIBS", "gCBS", "vCBS")),
        "ibs_cbs_cst": ibs_cbs_cst,
        "tax_classification_code": tax_classification_code,
    }


def _csll_withholding(bundle, pis_withheld, pis_value, cofins_withheld, cofins_value):
    """Return the CSLL part of ``vRetCSLL``.

    When PIS or COFINS is withheld, the national layout stores the sum of
    those withholdings and CSLL in ``vRetCSLL``. Otherwise the tag is CSLL.
    """
    deducted = 0.0
    if pis_withheld:
        deducted += pis_value or 0.0
    if cofins_withheld:
        deducted += cofins_value or 0.0
    if not deducted:
        return bundle
    remaining = round((bundle or 0.0) - deducted, 2)
    return remaining if remaining > 0 else 0.0


def _federal_tax_values(inf_dps):
    """Read PIS/COFINS and the federal withholdings from the DPS."""
    federal = _walk(inf_dps, "valores", "trib", "tribFed")
    pis_cofins = _node(federal, "piscofins")
    retention = _node_text(pis_cofins, "tpRetPisCofins") or ""
    pis_withheld = retention in _PIS_RETAINED
    cofins_withheld = retention in _COFINS_RETAINED
    pis_value = _amount(_node_text(pis_cofins, "vPis"))
    cofins_value = _amount(_node_text(pis_cofins, "vCofins"))
    return {
        "pis_cofins_cst": _node_text(pis_cofins, "CST"),
        "pis_cofins_base": _amount(_node_text(pis_cofins, "vBCPisCofins")),
        "pis_percent": _amount(_node_text(pis_cofins, "pAliqPis")),
        "pis_value": pis_value,
        "cofins_percent": _amount(_node_text(pis_cofins, "pAliqCofins")),
        "cofins_value": cofins_value,
        "pis_withheld": pis_withheld,
        "cofins_withheld": cofins_withheld,
        "irpj_wh_value": _amount(_node_text(federal, "vRetIRRF")),
        "csll_wh_value": _csll_withholding(
            _amount(_node_text(federal, "vRetCSLL")),
            pis_withheld,
            pis_value,
            cofins_withheld,
            cofins_value,
        ),
    }


def _party_address(node):
    """Read a national address (``end`` or the emitter ``enderNac``)."""
    if node is None:
        return {}
    national = _node(node, "endNac") or node
    return {
        "street_name": _node_text(node, "xLgr"),
        "street_number": _node_text(node, "nro"),
        "street2": _node_text(node, "xCpl"),
        "district": _node_text(node, "xBairro"),
        "zip": _digits(_node_text(national, "CEP")),
        "city_ibge": _digits(_node_text(national, "cMun")),
    }


def _party(node):
    if node is None:
        return {}
    legal_name = _node_text(node, "xNome")
    values = {
        "cnpj": _digits(_node_text(node, "CNPJ")),
        "cpf": _digits(_node_text(node, "CPF")),
        "legal_name": legal_name,
        "name": _node_text(node, "xFant") or legal_name,
        "im": _node_text(node, "IM"),
        "phone": _node_text(node, "fone"),
        "email": _node_text(node, "email"),
    }
    address = _node(node, "end") or _node(node, "enderNac")
    values.update(_party_address(address))
    return {key: value for key, value in values.items() if value}


def _provider_party(inf_nfse, inf_dps):
    """Provider from ``infDPS/prest``. Emitter data fills gaps only.

    ``tpEmit`` can be the taker, so ``infNFSe/emit`` is used only when its
    CNPJ is the same as the provider.
    """
    provider = _party(_node(inf_dps, "prest"))
    emitter = _party(_node(inf_nfse, "emit"))
    same_company = (
        emitter.get("cnpj") and emitter.get("cnpj") == provider.get("cnpj")
    ) or (emitter.get("cpf") and emitter.get("cpf") == provider.get("cpf"))
    if same_company:
        for key, value in emitter.items():
            provider.setdefault(key, value)
    return provider


def _service_value(inf_nfse, inf_dps):
    """Service amount from the DPS, with the net value as fallback."""
    service = _node_text(inf_dps, "valores", "vServPrest", "vServ")
    if service:
        return _amount(service)
    return _amount(_node_text(inf_nfse, "valores", "vLiq"))


def _parse_nfse_binding(xml_bytes):
    """Return ``infNFSe`` from the nfelib 1.01 binding, or None."""
    if isinstance(xml_bytes, bytes):
        try:
            xml_text = xml_bytes.decode()
        except UnicodeDecodeError:
            return None
    else:
        xml_text = xml_bytes
    try:
        document = Nfse.from_xml(xml_text, config=_NFSE_PARSER_CONFIG)
    except (ParserError, ValueError):
        return None
    # nfelib picks the binding by the XML root: once the NF-e bindings are
    # loaded (l10n_br_nfe does it), an NF-e comes back as an NfeProc.
    if not isinstance(document, Nfse):
        return None
    return document.infNFSe or None


def parse_nfse_xml(xml_bytes):
    """Map a national NFS-e XML to a dict. Returns None for other documents."""
    if not xml_bytes:
        return None
    inf_nfse = _parse_nfse_binding(xml_bytes)
    if inf_nfse is None:
        return None
    inf_dps = _walk(inf_nfse, "DPS", "infDPS")
    provider = _provider_party(inf_nfse, inf_dps)
    provider_cnpj = provider.get("cnpj") or provider.get("cpf") or ""
    provider_name = provider.get("legal_name") or provider.get("name")
    note_values = _node(inf_nfse, "valores")
    retention = _node_text(inf_dps, "valores", "trib", "tribMun", "tpRetISSQN")
    withheld = retention in {"2", "3"}
    issqn_percent = _amount(_node_text(note_values, "pAliqAplic"))
    issqn_value = _amount(_node_text(note_values, "vISSQN"))
    service = _walk(inf_dps, "serv", "cServ")
    return {
        "access_key": normalize_access_key(_node_text(inf_nfse, "Id")),
        "number": _node_text(inf_nfse, "nNFSe"),
        "serie": _node_text(inf_dps, "serie"),
        "emission_date": parse_nfse_datetime(
            _node_text(inf_dps, "dhEmi") or _node_text(inf_nfse, "dhProc")
        ),
        "provider_cnpj": provider_cnpj or False,
        "provider_name": provider_name,
        "provider": provider,
        "taker": _party(_node(inf_dps, "toma")),
        "tax_nature": _node_text(inf_nfse, "xTribNac"),
        "service_value": _service_value(inf_nfse, inf_dps),
        "description": _node_text(service, "xDescServ"),
        "issqn_base": _amount(_node_text(note_values, "vBC")),
        "issqn_percent": issqn_percent,
        "issqn_value": issqn_value,
        "issqn_wh_percent": issqn_percent if withheld else 0.0,
        "issqn_wh_value": issqn_value if withheld else 0.0,
        "service_lc116_code": _node_text(service, "cTribNac"),
        "service_nbs_code": _digits(_node_text(service, "cNBS")),
        "issqn_city_ibge": _digits(_node_text(inf_nfse, "cLocIncid")),
        "rps_number": _node_text(inf_dps, "nDPS"),
        **_ibs_cbs_values(inf_nfse, inf_dps, xml_bytes),
        **_federal_tax_values(inf_dps),
    }
