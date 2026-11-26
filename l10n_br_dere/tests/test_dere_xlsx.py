# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import zipfile
from io import BytesIO
from xml.etree import ElementTree as ET

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import DereCommon

SS_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _xlsx_sheet_names(data):
    with zipfile.ZipFile(BytesIO(data)) as archive:
        root = ET.fromstring(archive.read("xl/workbook.xml"))
        return [sheet.get("name") for sheet in root.findall("m:sheets/m:sheet", SS_NS)]


def _xlsx_text(data):
    with zipfile.ZipFile(BytesIO(data)) as archive:
        chunks = []
        names = archive.namelist()
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            chunks.extend(
                "".join(node.itertext()) for node in root.findall("m:si", SS_NS)
            )
        for name in names:
            if name.startswith("xl/worksheets/") and name.endswith(".xml"):
                chunks.append(archive.read(name).decode("utf-8"))
        return "\n".join(chunks)


@tagged("post_install", "-at_install")
class TestDereXlsx(DereCommon):
    def test_declaration_xlsx_includes_pgcc_and_trial(self):
        declaration = self._prepare_trial("2026-11")
        data = declaration._dere_xlsx_bytes()
        self.assertTrue(data.startswith(b"PK"))
        self.assertEqual(_xlsx_sheet_names(data), ["D-1011", "D-1101"])
        text = _xlsx_text(data)
        self.assertIn(self.fee_account.l10n_br_dere_cta, text)
        self.assertIn("cCta", text)
        self.assertIn("vMovDebt", text)
        action = declaration.action_download_xlsx()
        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertEqual(
            action["url"],
            f"/l10n_br_dere/xlsx/l10n_br_dere.declaration/{declaration.id}",
        )
        self.assertIn("2026-11", declaration._dere_xlsx_filename())
        self.assertIn("D-1101", declaration._dere_xlsx_filename())

    def test_d1011_event_xlsx_has_only_pgcc_sheet(self):
        declaration = self._create_declaration()
        self._table_period(declaration).action_generate_tables()
        event = self._event(declaration, "D-1011")
        data = event._dere_xlsx_bytes()
        self.assertEqual(_xlsx_sheet_names(data), ["D-1011"])
        self.assertIn(self.fee_account.l10n_br_dere_cta, _xlsx_text(data))
        action = event.action_download_xlsx()
        self.assertEqual(
            action["url"],
            f"/l10n_br_dere/xlsx/l10n_br_dere.event/{event.id}",
        )

    def test_xlsx_without_lines_raises(self):
        declaration = self._create_declaration()
        with self.assertRaises(UserError):
            declaration._dere_xlsx_bytes()
        with self.assertRaises(UserError):
            declaration.action_download_xlsx()
        self._table_period(declaration).action_generate_d1001()
        event = self._event(declaration, "D-1001")
        with self.assertRaises(UserError):
            event._dere_xlsx_bytes()
