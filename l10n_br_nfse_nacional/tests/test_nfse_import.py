# Copyright 2026 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pkg_resources
from nfelib.nfse.bindings.v1_0.dps_v1_00 import Dps

from odoo.tests import TransactionCase, tagged

from odoo.addons import l10n_br_nfse_nacional


# The import builds the remaining spec models on the fly, which must not happen
# inside an at_install test transaction: it would roll back their tables.
@tagged("post_install", "-at_install")
class NfseImportTest(TransactionCase):
    def test_import_dps(self):
        res_items = ("tests", "nfse", "v1_00", "DPS", "dps-regime-normal.xml")
        resource_path = "/".join(res_items)
        xml_stream = pkg_resources.resource_stream(
            l10n_br_nfse_nacional.__name__, resource_path
        )
        binding = Dps.from_xml(xml_stream.read().decode())

        doc = self.env["l10n_br_fiscal.document"].import_binding_nfse(
            binding, edoc_type="in", dry_run=True
        )
        # the DPS values must land on the fiscal document fields
        self.assertEqual(doc.document_number, "2")
        self.assertEqual(doc.document_serie, "00007")
