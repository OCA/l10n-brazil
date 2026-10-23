# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import os
import tempfile
import zipfile
from datetime import date
from unittest.mock import patch

from odoo.tests.common import BaseCase

from odoo.addons.l10n_br_hr_employee_ppe.lib.client import (
    CAEPIError,
    download_and_parse,
    normalize_ca,
)

SAMPLE_LINES = """\
NR Registro CA|DATA DE VALIDADE|SITUACAO|NR DO PROCESSO|CNPJ|\
RAZAO SOCIAL|NATUREZA|EQUIPAMENTO|DESCRICAO EQUIPAMENTO|\
MARCA CA|REFERENCIA|COR|APROVADO PARA LAUDO|RESTRICAO LAUDO|\
OBSERVACAO ANALISE LAUDO|CNPJ LABORATORIO|\
RAZAO SOCIAL LABORATORIO|NR LAUDO|NORMA
42016|30/12/2027|VÁLIDO|P1|C1|BSB PRODUTORA|Nacional|\
BOTINA - TIPO B||||CINZA|PROTEÇÃO DOS PÉS||||||NBR 12345
42016|30/12/2027|VÁLIDO|P1|C1|BSB PRODUTORA|Nacional|\
BOTINA - TIPO B||||PRETA|PROTEÇÃO DOS PÉS||||||NBR 12345
31469|23/05/2028|VÁLIDO|P2|C2|PLASTCOR|Nacional|\
CAPACETE CLASSE E|||||PROTEÇÃO DA CABEÇA||||||NBR 99999
10401|18/05/2014|VENCIDO|P3|C3|FABRICA ANTIGA|Nacional|\
LUVA|||||PROTEÇÃO DAS MÃOS||||||
10401|14/08/2026|VÁLIDO|P4|C3|FABRICA ANTIGA|Nacional|\
LUVA|||||PROTEÇÃO DAS MÃOS||||||
99999||CANCELADO|P5|C4|TESTE|Nacional|\
LUVA|||||TESTE||||||
"""


def _make_zip(content):
    path = tempfile.NamedTemporaryFile(suffix=".zip", delete=False).name
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("tgg_export_caepi.txt", content.encode("utf-8"))
    return path


class _FakeResponse:
    def __init__(self, path):
        self._fp = open(path, "rb")  # noqa: SIM115

    def read(self, n=-1):  # pylint: disable=method-required-super
        return self._fp.read(n)

    def close(self):
        self._fp.close()


def _mock_urlopen(zip_path):
    def side_effect(url, timeout=None):
        return _FakeResponse(zip_path)

    return side_effect


class TestNormalizeCa(BaseCase):
    def test_digits_only(self):
        self.assertEqual(normalize_ca("42016"), "42016")

    def test_with_dots(self):
        self.assertEqual(normalize_ca("42.016"), "42016")

    def test_with_prefix(self):
        self.assertEqual(normalize_ca("CA-00123"), "123")

    def test_leading_zeros(self):
        self.assertEqual(normalize_ca("00042016"), "42016")

    def test_empty(self):
        self.assertEqual(normalize_ca(""), "0")

    def test_none(self):
        self.assertEqual(normalize_ca(None), "0")


class TestDownloadAndParse(BaseCase):
    def test_dedup_keeps_latest(self):
        zip_path = _make_zip(SAMPLE_LINES)
        try:
            with patch(
                "odoo.addons.l10n_br_hr_employee_ppe.lib.client."
                "urllib.request.urlopen",
                side_effect=_mock_urlopen(zip_path),
            ):
                rows = download_and_parse()
        finally:
            os.unlink(zip_path)

        by_ca = {r["numero_ca"]: r for r in rows}

        self.assertIn("42016", by_ca)
        self.assertEqual(by_ca["42016"]["situacao"], "valid")
        self.assertEqual(by_ca["42016"]["data_validade"], date(2027, 12, 30))

        self.assertIn("10401", by_ca)
        self.assertEqual(by_ca["10401"]["data_validade"], date(2026, 8, 14))
        self.assertEqual(by_ca["10401"]["situacao"], "valid")

        self.assertIn("31469", by_ca)

        self.assertIn("99999", by_ca)
        self.assertIsNone(by_ca["99999"]["data_validade"])
        self.assertEqual(by_ca["99999"]["situacao"], "cancelled")

        self.assertEqual(len(rows), 4)

    def test_dateless_row_does_not_overwrite(self):
        lines = (
            "NR Registro CA|DATA DE VALIDADE|SITUACAO|NR DO PROCESSO|CNPJ|"
            "RAZAO SOCIAL|NATUREZA|EQUIPAMENTO|DESCRICAO EQUIPAMENTO|"
            "MARCA CA|REFERENCIA|COR|APROVADO PARA LAUDO|RESTRICAO LAUDO|"
            "OBSERVACAO ANALISE LAUDO|CNPJ LABORATORIO|"
            "RAZAO SOCIAL LABORATORIO|NR LAUDO|NORMA\n"
            "55555|01/06/2027|VÁLIDO|P|C|F|N|E||||C|A||||||N\n"
            "55555||VÁLIDO|P|C|F|N|E||||C|A||||||N\n"
        )
        zip_path = _make_zip(lines)
        try:
            with patch(
                "odoo.addons.l10n_br_hr_employee_ppe.lib.client."
                "urllib.request.urlopen",
                side_effect=_mock_urlopen(zip_path),
            ):
                rows = download_and_parse()
        finally:
            os.unlink(zip_path)

        by_ca = {r["numero_ca"]: r for r in rows}
        self.assertEqual(by_ca["55555"]["data_validade"], date(2027, 6, 1))

    def test_empty_zip_raises(self):
        path = tempfile.NamedTemporaryFile(suffix=".zip", delete=False).name
        with zipfile.ZipFile(path, "w"):
            pass
        with self.assertRaises(CAEPIError):
            with patch(
                "odoo.addons.l10n_br_hr_employee_ppe.lib.client."
                "urllib.request.urlopen",
                side_effect=_mock_urlopen(path),
            ):
                download_and_parse()
        os.unlink(path)
