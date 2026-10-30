# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Download and parse the MTE public CAEPI export.

The Ministério do Trabalho publishes a pipe-delimited ZIP on its FTP server
containing every CA ever issued (~125 k rows, ~42 k unique CAs).  This module
downloads, extracts and deduplicates it into a list of dicts ready for the
Odoo model.

No external dependency beyond the standard library.
"""

import io
import logging
import os
import re
import tempfile
import urllib.request
import zipfile
from datetime import datetime

_logger = logging.getLogger(__name__)

DEFAULT_FTP_URL = (
    "ftp://ftp.mtps.gov.br/portal/fiscalizacao/"
    "seguranca-e-saude-no-trabalho/caepi/tgg_export_caepi.zip"
)

_COL_CA = "NR Registro CA"
_COL_VALIDADE = "DATA DE VALIDADE"
_COL_SITUACAO = "SITUACAO"
_COL_EQUIPAMENTO = "EQUIPAMENTO"
_COL_FABRICANTE = "RAZAO SOCIAL"
_COL_CNPJ = "CNPJ"
_COL_NATUREZA = "NATUREZA"
_COL_NORMA = "NORMA"
_COL_APROVADO = "APROVADO PARA LAUDO"

_DATE_FMT = "%d/%m/%Y"
_DIGITS_RE = re.compile(r"\D")


class CAEPIError(Exception):
    pass


def normalize_ca(raw):
    """Strip non-digits and leading zeros."""
    digits = _DIGITS_RE.sub("", raw or "")
    return digits.lstrip("0") or "0"


def _parse_date(raw):
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, _DATE_FMT).date()
    except ValueError:
        return None


def download_and_parse(url=DEFAULT_FTP_URL, timeout=120):
    """Download the CAEPI ZIP and return deduplicated rows.

    When the same CA appears on multiple lines (different laudos), the row
    with the latest ``data_validade`` wins.
    """
    _logger.info("CAEPI: downloading from %s", url)
    tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    tmp_path = tmp.name
    tmp.close()
    try:
        resp = urllib.request.urlopen(url, timeout=timeout)
        with open(tmp_path, "wb") as fp:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                fp.write(chunk)
        resp.close()
    except Exception as exc:
        _cleanup(tmp_path)
        raise CAEPIError("Failed to download MTE file: %s" % exc) from exc

    try:
        rows = _parse_zip(tmp_path)
    finally:
        _cleanup(tmp_path)
    return rows


def _cleanup(path):
    try:
        os.unlink(path)
    except OSError:
        _logger.debug("Could not remove temp file %s", path)


def _parse_zip(zip_path):
    try:
        zf = zipfile.ZipFile(zip_path)
    except zipfile.BadZipFile as exc:
        raise CAEPIError("Corrupt ZIP file: %s" % exc) from exc

    with zf:
        names = zf.namelist()
        if not names:
            raise CAEPIError("Empty ZIP file")
        txt_name = next(
            (n for n in names if n.endswith((".txt", ".csv"))),
            names[0],
        )
        stream = io.TextIOWrapper(zf.open(txt_name), encoding="utf-8", errors="replace")
        return _parse_stream(stream)


def _parse_stream(stream):
    header_line = stream.readline().strip()
    if not header_line:
        raise CAEPIError("Empty data file")

    header = [col.strip() for col in header_line.split("|")]
    col_idx = {name: i for i, name in enumerate(header)}
    expected_cols = len(header)

    def _get(fields, col_name):
        idx = col_idx.get(col_name)
        if idx is None or idx >= len(fields):
            return ""
        return fields[idx].strip()

    best = {}
    skipped = 0
    total = 0
    for line in stream:
        line = line.strip()
        if not line:
            continue
        total += 1
        fields = line.split("|")

        if len(fields) != expected_cols:
            skipped += 1
            continue

        ca_raw = _get(fields, _COL_CA)
        if not ca_raw or not ca_raw.strip().isdigit():
            skipped += 1
            continue

        ca = normalize_ca(ca_raw)
        validade = _parse_date(_get(fields, _COL_VALIDADE))

        prev = best.get(ca)
        if prev:
            prev_date = prev["data_validade"]
            if prev_date and validade and prev_date >= validade:
                continue
            if prev_date and not validade:
                continue

        situacao_raw = _get(fields, _COL_SITUACAO)
        situacao_map = {
            "VÁLIDO": "valid",
            "VENCIDO": "expired",
            "SUSPENSO": "suspended",
            "CANCELADO": "cancelled",
        }
        situacao = situacao_map.get(situacao_raw)
        if not situacao:
            _logger.warning("CAEPI: unknown status %r for CA %s", situacao_raw, ca)
            skipped += 1
            continue

        best[ca] = {
            "numero_ca": ca,
            "situacao": situacao,
            "data_validade": validade,
            "equipamento": _get(fields, _COL_EQUIPAMENTO)[:256],
            "fabricante": _get(fields, _COL_FABRICANTE)[:256],
            "cnpj_fabricante": _get(fields, _COL_CNPJ)[:20],
            "natureza": _get(fields, _COL_NATUREZA)[:64],
            "norma": _get(fields, _COL_NORMA)[:256],
            "aprovado_para": _get(fields, _COL_APROVADO)[:512],
        }

    if skipped:
        _logger.warning("CAEPI: %d lines skipped (bad format)", skipped)
    _logger.info("CAEPI: parsed %d unique CAs from %d lines", len(best), total)
    return list(best.values())
