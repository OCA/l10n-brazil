# Copyright 2020 KMEE INFORMATICA LTDA
#   Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import io
import logging
import os
from datetime import datetime

from xmldiff import main

from odoo.tools import config

from odoo.addons.l10n_br_nfse.tests.test_fiscal_document_nfse_common import (
    TestFiscalDocumentNFSeCommon,
)

from ... import l10n_br_nfse_paulistana

_logger = logging.getLogger(__name__)


class TestFiscalDocumentNFSePaulistana(TestFiscalDocumentNFSeCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["res.lang"]._activate_lang("pt_BR")
        cls.company.provedor_nfse = "paulistana"

    def test_nfse_paulistana(self):
        """Test NFS-e same state."""

        xml_path = os.path.join(
            l10n_br_nfse_paulistana.__path__[0], "tests", "nfse", "paulistana.xml"
        )

        self.nfse_same_state.rps_number = "50"
        self.nfse_same_state.document_number = "50"

        for line in self.nfse_same_state.fiscal_line_ids:
            line._onchange_fiscal_taxes()

        self.nfse_same_state.action_document_confirm()

        self.nfse_same_state.document_date = datetime.strptime(
            "2020-06-04T11:58:46", "%Y-%m-%dT%H:%M:%S"
        )
        self.nfse_same_state.date_in_out = datetime.strptime(
            "2020-06-04T11:58:46", "%Y-%m-%dT%H:%M:%S"
        )

        self.nfse_same_state.with_context(lang="pt_BR")._document_export()

        output = os.path.join(
            config["data_dir"],
            "filestore",
            self.cr.dbname,
            self.nfse_same_state.send_file_id.store_fname,
        )
        _logger.info("XML file saved at %s", output)

        diff = main.diff_files(xml_path, output)
        _logger.info("Diff with expected XML (if any): %s", diff)

        assert len(diff) == 0

    def test_serialize_nfse_paulistana(self):
        """Test serialization of NFS-e Paulistana."""
        self.nfse_same_state.rps_number = "50"
        self.nfse_same_state.document_number = "50"

        for line in self.nfse_same_state.fiscal_line_ids:
            line._onchange_fiscal_taxes()

        self.nfse_same_state.action_document_confirm()

        serialized = self.nfse_same_state.serialize_nfse_paulistana()
        self.assertIsNotNone(serialized)
        self.assertTrue(hasattr(serialized, "Cabecalho"))
        self.assertTrue(hasattr(serialized, "RPS"))
        self.assertEqual(len(serialized.RPS), 1)

    def test_serialize_nfse_paulistana_v03(self):
        """Test serialization with the tax reform layout (nfselib v03)."""
        self.nfse_same_state.rps_number = "50"
        self.nfse_same_state.document_number = "50"

        for line in self.nfse_same_state.fiscal_line_ids:
            line._onchange_fiscal_taxes()

        self.nfse_same_state.action_document_confirm()

        serialized = self.nfse_same_state.serialize_nfse_paulistana(nfse_version="v03")
        self.assertEqual(
            type(serialized).__module__, "nfselib.paulistana.v03.PedidoEnvioLoteRPS"
        )
        self.assertEqual(serialized.Cabecalho.Versao, 2)
        self.assertEqual(len(serialized.RPS), 1)
        rps = serialized.RPS[0]
        # The v03 bindings apply b64encode when exporting Assinatura: the
        # value must be bytes, otherwise the export raises TypeError.
        self.assertIsInstance(rps.Assinatura, bytes)
        # Required fields that only exist in the tax reform layout.
        self.assertIsNotNone(rps.ValorFinalCobrado)
        self.assertIsNotNone(rps.IBSCBS)

        buf = io.StringIO()
        serialized.export(buf, 0, pretty_print=True)
        xml = buf.getvalue()
        self.assertIn('Versao="2"', xml)
        self.assertIn("<Discriminacao>", xml)

    def test_map_taxation_rps(self):
        """Test mapping of taxation RPS."""
        self.assertEqual(self.nfse_same_state._map_taxation_rps("1"), "T")
        self.assertEqual(self.nfse_same_state._map_taxation_rps("2"), "F")
        self.assertEqual(self.nfse_same_state._map_taxation_rps("3"), "A")
        self.assertEqual(self.nfse_same_state._map_taxation_rps("4"), "R")
        self.assertEqual(self.nfse_same_state._map_taxation_rps("5"), "X")
        self.assertEqual(self.nfse_same_state._map_taxation_rps("6"), "X")

    def test_map_type_rps(self):
        """Test mapping of RPS type."""
        self.assertEqual(self.nfse_same_state._map_type_rps("1"), "RPS")
        self.assertEqual(self.nfse_same_state._map_type_rps("2"), "RPS-M")
        self.assertEqual(self.nfse_same_state._map_type_rps("3"), "RPS-C")

    def test_map_provision_municipality(self):
        """Test mapping of provision municipality."""
        self.assertIsNone(
            self.nfse_same_state._map_provision_municipality("1", "3550308")
        )
        self.assertEqual(
            self.nfse_same_state._map_provision_municipality("2", "3550308"), "3550308"
        )
