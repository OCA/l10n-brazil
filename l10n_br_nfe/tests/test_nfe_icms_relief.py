# Copyright (C) 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import nfelib
import pkg_resources
from nfelib.nfe.bindings.v4_0.leiaute_nfe_v4_00 import TnfeProc

from odoo.tests import TransactionCase

ICMS00 = """<ICMS00>
              <orig>0</orig>
              <CST>00</CST>
              <modBC>0</modBC>
              <vBC>50.60</vBC>
              <pICMS>12.00</pICMS>
              <vICMS>6.07</vICMS>
            </ICMS00>"""

ICMS20 = """<ICMS20>
              <orig>0</orig>
              <CST>20</CST>
              <modBC>0</modBC>
              <pRedBC>10.0000</pRedBC>
              <vBC>45.54</vBC>
              <pICMS>12.00</pICMS>
              <vICMS>5.46</vICMS>
              <vICMSDeson>0.61</vICMSDeson>
              <motDesICMS>9</motDesICMS>{ind_deduz_deson}
            </ICMS20>"""


class NFeIcmsReliefTest(TransactionCase):
    def _import_nfe(self, ind_deduz_deson=None):
        resource_path = "/".join(
            (
                "nfe",
                "samples",
                "v4_0",
                "leiauteNFe",
                "35180834128745000152550010000474281920007498-nfe.xml",
            )
        )
        nfe_stream = pkg_resources.resource_stream(nfelib.__name__, resource_path)
        xml = nfe_stream.read().decode()
        tag = (
            f"\n              <indDeduzDeson>{ind_deduz_deson}</indDeduzDeson>"
            if ind_deduz_deson
            else ""
        )
        self.assertIn(ICMS00, xml)
        xml = xml.replace(ICMS00, ICMS20.format(ind_deduz_deson=tag), 1)
        binding = TnfeProc.from_xml(xml)
        nfe = self.env["l10n_br_fiscal.document"].import_binding_nfe(
            binding, edoc_type="in", dry_run=False
        )
        return nfe.fiscal_line_ids.sorted("id")[0]

    def test_import_ind_deduz_deson(self):
        line = self._import_nfe(ind_deduz_deson="1")
        self.assertEqual(line.icms_relief_type, "1")
        self.assertEqual(line.icms_relief_value, 0.61)
        self.assertEqual(line.icms_relief_id.code, "9")

    def test_import_without_ind_deduz_deson(self):
        line = self._import_nfe()
        self.assertEqual(line.icms_relief_type, "0")
        self.assertEqual(line.icms_relief_value, 0.61)

    def test_export_ind_deduz_deson(self):
        line = self._import_nfe(ind_deduz_deson="1")
        export_dict = {}
        line._export_fields_nfe_40_icms([], None, export_dict)
        self.assertEqual(export_dict["ICMS20"].indDeduzDeson, "1")
        self.assertEqual(export_dict["ICMS20"].vICMSDeson, "0.61")
