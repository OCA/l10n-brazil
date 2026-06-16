# Copyright 2026 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# Copyright 2026 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pkg_resources

from odoo.tests import TransactionCase

from odoo.addons import l10n_br_nfse_nacional


class NfseImportTest(TransactionCase):
    def test_import_dps(self):
        try:
            from nfelib.nfse.bindings.v1_0.tipos_complexos_v1_00 import DPS
        except ImportError:
            return  # Skip gracefully if nfelib nfse national schema isn't present

        res_items = ("tests", "nfse", "v1_00", "DPS", "dps-regime-normal.xml")
        resource_path = "/".join(res_items)
        xml_stream = pkg_resources.resource_stream(
            l10n_br_nfse_nacional.__name__, resource_path
        )
        binding = DPS.from_xml(xml_stream.read().decode())

        doc = self.env["l10n_br_fiscal.document"].import_binding_nfse(
            binding, edoc_type="in", dry_run=True
        )
        self.assertEqual(doc.nfse10_nDPS, "2")
        self.assertEqual(doc.nfse10_serie, "00007")
