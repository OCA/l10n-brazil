# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

import pkg_resources
from nfelib.cte.bindings.v4_0.cte_v4_00 import Tcte

from odoo.models import NewId
from odoo.tests import TransactionCase

from odoo.addons import l10n_br_cte

_logger = logging.getLogger(__name__)


class CTeImportTest(TransactionCase):
    def test_import_in_cte_dry_run(self):
        res_items = (
            "tests",
            "cte",
            "v4_00",
            "leiauteCTe",
            "CTe51160824686092000173570010000000031000000024.xml",
        )

        resource_path = "/".join(res_items)
        cte_stream = pkg_resources.resource_stream(l10n_br_cte.__name__, resource_path)
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
            "tests",
            "cte",
            "v4_00",
            "leiauteCTe",
            "CTe51160724686092000173570010000000031000000024.xml",
        )

        resource_path = "/".join(res_items)
        cte_stream = pkg_resources.resource_stream(l10n_br_cte.__name__, resource_path)
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

        self.assertEqual(cte.cte40_UFIni, "MT")
        self.assertEqual(cte.cte40_UFFim, "MT")

        self.assertEqual(cte.cte40_verProc, "2.0.1")

    def test_import_out_cte(self):
        "(can be useful after an ERP migration)"
