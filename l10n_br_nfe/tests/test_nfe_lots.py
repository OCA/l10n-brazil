# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
import re
from datetime import date

from odoo.addons import l10n_br_nfe
from odoo.addons.l10n_br_fiscal_edi.tests.common import KEY_1, EdiImportCase
from odoo.addons.l10n_br_fiscal_edi.tools import EdiLot

FIXTURE_DIR = os.path.join(
    l10n_br_nfe.__path__[0], "tests", "nfe", "v4_00", "leiauteNFe"
)
FIXTURE_DEST = re.compile(rb"(<dest>\s*)<(?:CNPJ|CPF)>\d+</(?:CNPJ|CPF)>")
RASTRO = (
    b"<rastro><nLote>L-A</nLote><qLote>0.5</qLote><dFab>2026-01-10</dFab>"
    b"<dVal>2027-01-10</dVal></rastro>"
    b"<rastro><nLote>L-B</nLote><qLote>0.5</qLote><dVal>2027-06-30</dVal></rastro>"
)


class TestNfeLots(EdiImportCase):
    def _import(self, lots=b""):
        with open(os.path.join(FIXTURE_DIR, f"NFe{KEY_1}.xml"), "rb") as xml_file:
            content = xml_file.read()
        recipient = self.company.partner_id.cnpj_cpf_stripped
        content = FIXTURE_DEST.sub(rb"\1<CNPJ>%s</CNPJ>" % recipient.encode(), content)
        content = content.replace(b"</prod>", lots + b"</prod>", 1)
        documents, errors, _warnings = self.Document._edi_import_files(
            [("nfe.xml", content)]
        )
        self.assertFalse(errors)
        return documents.fiscal_line_ids

    def test_the_lots_of_the_item_are_read_from_the_file(self):
        line = self._import(RASTRO)

        self.assertEqual(
            line._edi_get_lots(),
            [
                EdiLot("L-A", 0.5, date(2026, 1, 10), date(2027, 1, 10)),
                EdiLot("L-B", 0.5, None, date(2027, 6, 30)),
            ],
        )

    def test_an_item_without_lots_declares_none(self):
        self.assertEqual(self._import()._edi_get_lots(), [])
