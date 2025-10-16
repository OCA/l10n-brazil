# @ 2020 KMEE INFORMATICA LTDA - www.kmee.com.br -
# Copyright 2025 - TODAY Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import nfelib
import pkg_resources
from nfelib.mdfe.bindings.v3_0.mdfe_v3_00 import Tmdfe

from odoo.models import NewId
from odoo.tests import TransactionCase


class MDFeImportTest(TransactionCase):
    def test_import_in_mdfe_dry_run(self):
        res_items = (
            "mdfe",
            "samples",
            "v3_0",
            "50170876063965000276580010000011311421039568-mdfe.xml",
        )

        resource_path = "/".join(res_items)
        mdfe_stream = pkg_resources.resource_stream(nfelib.__name__, resource_path)
        binding = Tmdfe.from_xml(mdfe_stream.read().decode())
        mdfe = self.env["l10n_br_fiscal.document"].import_binding_mdfe(
            binding, edoc_type="in", dry_run=True
        )
        assert isinstance(mdfe.id, NewId)
        self._check_mdfe(mdfe)

    def test_import_in_mdfe(self):
        res_items = (
            "mdfe",
            "samples",
            "v3_0",
            "50170876063965000276580010000011311421039568-mdfe.xml",
        )
        resource_path = "/".join(res_items)
        mdfe_stream = pkg_resources.resource_stream(nfelib.__name__, resource_path)
        binding = Tmdfe.from_xml(mdfe_stream.read().decode())
        for item in binding.infMDFe.infDoc.infMunDescarga:
            # complete sample data to avoid empty state_id error:
            item.cMunDescarga = "1200013"
        mdfe = self.env["l10n_br_fiscal.document"].import_binding_mdfe(
            binding, edoc_type="in", dry_run=False
        )
        assert isinstance(mdfe.id, int)
        self._check_mdfe(mdfe)

    def _check_mdfe(self, mdfe):
        self.assertEqual(type(mdfe)._name, "l10n_br_fiscal.document")
        self.assertEqual(
            mdfe.document_type_id, self.env.ref("l10n_br_fiscal.document_58")
        )
        self.assertEqual(mdfe.document_number, "1131")
        # ide
        self.assertEqual(mdfe.mdfe30_cMDF, "42103956")
        self.assertEqual(mdfe.mdfe30_infMunCarrega[0].mdfe30_xMunCarrega, "IVINHEMA")
        self.assertEqual(mdfe.mdfe30_UFIni, "MS")
        self.assertEqual(mdfe.mdfe30_UFFim, "PR")
        self.assertEqual(mdfe.mdfe30_modal, "1")
        self.assertEqual(mdfe.mdfe30_qNFe, 2)
        self.assertEqual(mdfe.mdfe30_vCarga, 96800.0)
        self.assertEqual(mdfe.mdfe30_qCarga, 44264.0)
        self.assertEqual(mdfe.mdfe30_cUnid, "01")

        self.assertEqual(len(mdfe.mdfe30_infMunCarrega), 1)
        self.assertEqual(mdfe.mdfe30_infMunCarrega[0].mdfe30_xMunCarrega, "IVINHEMA")
        self.assertEqual(len(mdfe.mdfe30_infMunDescarga), 1)
        if isinstance(mdfe.id, int):
            self.assertEqual(
                mdfe.mdfe30_infMunDescarga[0].city_id,
                self.env.ref("l10n_br_base.city_1200013"),
            )

        # modal  # TODO implement modal mapping
        # self.assertEqual(mdfe.mdfe30_placa, "XXX1228")
        # self.assertEqual(mdfe.mdfe30_tara, "0")
        # self.assertEqual(mdfe.mdfe30_condutor[0].mdfe30_xNome, "TESTE")
        # self.assertEqual(len(mdfe.mdfe30_veicReboque), 0)

        self.assertEqual(mdfe.mdfe30_verProc, "UNICO V8.0")

    def test_import_out_mdfe(self):
        "(can be useful after an ERP migration)"
