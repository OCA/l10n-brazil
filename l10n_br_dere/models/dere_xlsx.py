# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re
from io import BytesIO

from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools.misc import xlsxwriter

D1011_HEADERS = [
    "cCta",
    "cCtaInterna",
    "cDbrMista",
    "nomeCta",
    "indCta",
    "descCta",
    "cCtaSup",
    "cCtaRef",
    "nivelCta",
    "natCta",
    "codNat",
    "codTrib",
    "indTribISS",
    "idLeiDisp",
    "iniVig",
    "fimVig",
]
D1101_HEADERS = [
    "cCta",
    "natSaldoInic",
    "vSaldoInic",
    "vMovDebt",
    "vAjusteDebt",
    "vMovCred",
    "vAjusteCred",
    "natSaldoFinal",
    "vSaldoFinal",
    "natVApur",
    "vApur",
]
D1106_HEADERS = [
    "cCta",
    "idAtivo",
    "descAtivo",
    "vSaldoInic",
    "vRendPerReceb",
    "vVarMensal",
    "vPrincLiqResg",
    "vRendLiqResg",
    "vSaldoFinal",
    "vApur",
]
D1121_HEADERS = [
    "tpDFe",
    "chDFe",
    "dtEmi",
    "tpAtiv",
    "vOper",
    "vDedTotal",
    "vDed",
]
D1121_ITEM_HEADERS = [
    "chDFe",
    "nItem",
    "vItem",
    "vItemDedTotal",
    "vItemDed",
]
D9101_HEADERS = [
    "codTrib",
    "indTribISS",
    "vApurTot",
    "local_v_apur",
]


def _xlsx_cell(value):
    if value is False or value is None:
        return ""
    return value


class DereXlsxMixin(models.AbstractModel):
    _name = "l10n_br_dere.xlsx.mixin"
    _description = "DeRE XLSX export mixin"

    def _dere_xlsx_sheets(self):
        self.ensure_one()
        return []

    def _dere_xlsx_period_label(self):
        self.ensure_one()
        return ""

    def _dere_xlsx_safe_token(self, value):
        token = re.sub(r"[^0-9A-Za-z._-]+", "_", str(value or "")).strip("_")
        return token or "DeRE"

    def _dere_xlsx_filename(self):
        self.ensure_one()
        titles = [
            title.replace(" ", "")
            for title, _headers, _rows in self._dere_xlsx_sheets()
        ]
        company = self._dere_xlsx_safe_token(self.company_id.name)
        period = self._dere_xlsx_safe_token(self._dere_xlsx_period_label())
        events = "_".join(self._dere_xlsx_safe_token(title) for title in titles)
        return f"DeRE_{company}_{period}_{events}.xlsx"

    def _dere_xlsx_records_sheet(self, title, headers, records):
        if not records:
            return []
        rows = []
        for rec in records:
            vals = rec._to_xml_vals()
            rows.append({key: vals.get(key) for key in headers})
        return [(title, headers, rows)]

    def _dere_xlsx_pgcc_sheets(self, accounts):
        return self._dere_xlsx_records_sheet("D-1011", D1011_HEADERS, accounts)

    def _dere_xlsx_trial_sheets(self, lines):
        return self._dere_xlsx_records_sheet("D-1101", D1101_HEADERS, lines)

    def _dere_xlsx_reserve_sheets(self, lines):
        return self._dere_xlsx_records_sheet("D-1106", D1106_HEADERS, lines)

    def _dere_xlsx_deduction_sheets(self, lines):
        if not lines:
            return []
        docs = []
        items = []
        for line in lines:
            vals = line._to_xml_vals()
            docs.append({key: vals.get(key) for key in D1121_HEADERS})
            for item in vals.get("items") or []:
                row = {key: item.get(key) for key in D1121_ITEM_HEADERS}
                row["chDFe"] = vals.get("chDFe") or ""
                items.append(row)
        sheets = [("D-1121", D1121_HEADERS, docs)]
        if items:
            sheets.append(("D-1121 Items", D1121_ITEM_HEADERS, items))
        return sheets

    def _dere_xlsx_total_sheets(self, totals):
        if not totals:
            return []
        rows = [
            {
                "codTrib": rec.dere12_codTrib,
                "indTribISS": rec.dere12_indTribISS,
                "vApurTot": rec.dere12_vApurTot,
                "local_v_apur": rec.local_v_apur,
            }
            for rec in totals
        ]
        return [("D-9101", D9101_HEADERS, rows)]

    def _dere_xlsx_bytes(self):
        self.ensure_one()
        sheets = self._dere_xlsx_sheets()
        if not sheets:
            raise UserError(_("Generate the DeRE event before downloading the XLSX."))
        if xlsxwriter is None:
            raise UserError(_("XlsxWriter is required to download DeRE spreadsheets."))
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        header_fmt = workbook.add_format({"bold": True})
        for title, headers, rows in sheets:
            sheet = workbook.add_worksheet(title[:31])
            for col, header in enumerate(headers):
                sheet.write(0, col, header, header_fmt)
            for row_idx, row in enumerate(rows, start=1):
                for col, header in enumerate(headers):
                    sheet.write(row_idx, col, _xlsx_cell(row.get(header)))
        workbook.close()
        return output.getvalue()

    def action_download_xlsx(self):
        self.ensure_one()
        if not self._dere_xlsx_sheets():
            raise UserError(_("Generate the DeRE event before downloading the XLSX."))
        return {
            "type": "ir.actions.act_url",
            "url": f"/l10n_br_dere/xlsx/{self._name}/{self.id}",
            "target": "self",
        }
