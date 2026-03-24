# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# Copyright 2025 - TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import pkg_resources
from nfelib.cte.bindings.v4_0.cte_v4_00 import Tcte

from odoo.models import NewId
from odoo.tests import TransactionCase

from odoo.addons import l10n_br_cte


class CTeImportTest(TransactionCase):
    def test_import_in_cte_dry_run(self):
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
        self.env["l10n_br_fiscal.document"].search(
            [("document_number", "=", 571)]
        ).unlink()
        cte = self.env["l10n_br_fiscal.document"].import_binding_cte(
            binding, edoc_type="in", dry_run=True
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
        self.env["l10n_br_fiscal.document"].search(
            [("document_number", "=", 571)]
        ).unlink()
        cte = self.env["l10n_br_fiscal.document"].import_binding_cte(
            binding, edoc_type="in", dry_run=False
        )

        assert isinstance(cte.id, int)
        self._check_cte(cte)

    def _check_cte(self, cte):
        self.assertEqual(type(cte)._name, "l10n_br_fiscal.document")
        self.assertEqual(
            cte.document_type_id, self.env.ref("l10n_br_fiscal.document_57")
        )
        self.assertEqual(cte.document_number, "571")

        self.assertEqual(cte.cte40_UFIni, "MT")
        self.assertEqual(cte.cte40_UFFim, "MT")
        self.assertEqual(cte.cte40_modal, "01")
        self.assertEqual(cte.cte40_vCarga, 79400)
        self.assertEqual(cte.cte40_proPred, "GADO")

        self.assertEqual(cte.partner_id.name, "P J TOSTA TRANSPORTES ME")
        if isinstance(cte.id, int):
            self.assertTrue(
                cte.partner_id.vat in ("24.686.092/0001-73", "24686092000173")
            )
            self.assertEqual(cte.partner_id.legal_name, "P J TOSTA TRANSPORTES ME")
            self.assertEqual(cte.partner_id.street_name, "RUA RENATO JOSE DOS SANTOS")
            self.assertEqual(cte.partner_id.zip, "78132-712")
            self.assertEqual(cte.partner_id.cte40_CEP, "78132712")
            self.assertEqual(cte.partner_id.city_id.name, "Várzea Grande")

        # now we check that company_id is unchanged
        self.assertEqual(cte.company_id, self.env.ref("base.main_company"))

        self.assertEqual(cte.cte40_verProc, "2.0.1")

        # lines data
        self.assertEqual(len(cte.fiscal_line_ids), 1)
        self.assertEqual(cte.fiscal_line_ids[0].quantity, 1)
        self.assertEqual(cte.fiscal_line_ids[0].price_unit, 4000.0)

    def test_import_out_cte(self):
        "(can be useful after an ERP migration)"
