# @ 2020 KMEE INFORMATICA LTDA - www.kmee.com.br -
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

import nfelib
import pkg_resources
from nfelib.cte.bindings.v4_0.cte_v4_00 import Tcte

from odoo.models import NewId
from odoo.tests import SavepointCase

_logger = logging.getLogger(__name__)


class CTeImportTest(SavepointCase):
    def test_import_in_cte_dry_run(self):
        res_items = (
            "cte",
            "samples",
            "v4_0",
            "51160624686092000173570010000000031000000020-cte.XML",
        )

        resource_path = "/".join(res_items)
        cte_stream = pkg_resources.resource_stream(nfelib.__name__, resource_path)
        binding = Tcte.from_xml(cte_stream.read().decode())

        cte = (
            self.env["cte.40.tcte_infcte"]
            .with_context(tracking_disable=True, edoc_type="in")
            .build_from_binding("cte", "40", binding.infCte, dry_run=True)
        )
        assert isinstance(cte.id, NewId)
        self._check_cte(cte)

    def test_import_in_cte(self):
        res_items = (
            "cte",
            "samples",
            "v4_0",
            "51160624686092000173570010000000031000000020-cte.XML",
        )
        resource_path = "/".join(res_items)
        cte_stream = pkg_resources.resource_stream(nfelib.__name__, resource_path)
        binding = Tcte.from_xml(cte_stream.read().decode())
        cte = (
            self.env["cte.40.tcte_infcte"]
            .with_context(tracking_disable=True, edoc_type="in")
            .build_from_binding("cte", "40", binding.infCte, dry_run=False)
        )

        assert isinstance(cte.id, int)
        self._check_cte(cte)

    def _check_cte(self, cte):
        self.assertEqual(type(cte)._name, "l10n_br_fiscal.document")

        # ide
        self.assertEqual(cte.cte40_nCT, "3")
        # self.assertEqual(cte.cte40_infMunCarrega[0].cte40_xMunCarrega, "IVINHEMA")
        self.assertEqual(cte.cte40_UFIni, "MT")
        self.assertEqual(cte.cte40_UFFim, "MT")

        # # modal
        # self.assertEqual(cte.cte40_placa, "XXX1228")
        # self.assertEqual(cte.cte40_tara, "0")
        # self.assertEqual(cte.cte40_condutor[0].cte40_xNome, "TESTE")
        # self.assertEqual(len(cte.cte40_veicReboque), 0)

        self.assertEqual(cte.cte40_verProc, "104")

    def test_import_out_cte(self):
        "(can be useful after an ERP migration)"
