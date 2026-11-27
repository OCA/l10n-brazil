# Copyright 2026 Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import gzip
import re
import zlib

from lxml import etree

from odoo.addons.l10n_br_nfse.services.nfse_xml import (
    NfseNacionalBinding,
    _is_nfse_document,
    _local_name,
    _text,
    normalize_access_key,
    parse_nfse_xml,
)

from ..constants.nfse_dfe import (
    NFSE_CANCEL_EVENT_CODES,
    NFSE_CANCEL_EVENT_NAMES,
    NFSE_EVENT_CODE_BY_NAME,
)


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
    }


def xml_root_is_nfse(xml_bytes):
    if not xml_bytes:
        return False
    try:
        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError:
        return False
    return _is_nfse_document(root)
