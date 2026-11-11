# Copyright 2026 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import importlib

from nfelib.nfse.bindings.v1_0.dps_v1_01 import Dps

from odoo.tests import TransactionCase, tagged

from odoo.addons import l10n_br_nfse_nacional


# The import builds the remaining spec models on the fly, which must not happen
# inside an at_install test transaction: it would roll back their tables.
@tagged("post_install", "-at_install")
class NfseImportTest(TransactionCase):
    def _import(self):
        res_items = ("tests", "nfse", "v1_00", "DPS", "dps-regime-normal.xml")
        resource_path = "/".join(res_items)
        dps_file = importlib.resources.files(l10n_br_nfse_nacional.__name__).joinpath(
            resource_path
        )
        with dps_file.open("rb") as fp:
            binding = Dps.from_xml(fp.read().decode())
        return self.env["l10n_br_fiscal.document"].import_binding_nfse(
            binding, edoc_type="in", dry_run=True
        )

    def test_import_dps(self):
        doc = self._import()
        # the DPS values must land on the fiscal document fields
        self.assertEqual(doc.document_number, "2")
        self.assertEqual(doc.document_serie, "00007")

    def test_import_declares_the_service_on_the_document(self):
        """The groups of the DPS land on the document, not on loose records.

        The service is stacked on the fiscal document: serv and valores are
        not two records to be reconciled anymore.
        """
        doc = self._import()
        self.assertFalse(doc.fiscal_line_ids)
        self.assertEqual(doc.nfse10_cTribNac, "010101")
        self.assertEqual(doc.nfse10_cNBS, "111111111")
        self.assertEqual(doc.nfse10_cLocPrestacao, "4202404")
        self.assertEqual(doc.nfse10_xDescServ, "Teste de NF Nacional com imposto")
        self.assertEqual(doc.nfse10_vServ, "20.00")
        self.assertEqual(doc.nfse10_vRetCP, "0.40")
        self.assertEqual(doc.nfse10_tribISSQN, "1")
        self.assertEqual(doc.nfse10_CST, "00")
        self.assertEqual(doc.nfse10_pTotTribFed, "0.00")
        self.assertEqual(doc.nfse10_prest, doc.company_id)
