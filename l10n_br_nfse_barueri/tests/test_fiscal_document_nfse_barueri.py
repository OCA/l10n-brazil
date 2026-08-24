# Copyright 2020 KMEE INFORMATICA LTDA
#   Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import os
from datetime import datetime
from unittest.mock import MagicMock, patch

from xmldiff import main

from odoo.tools import config

from odoo.addons.l10n_br_nfse.tests.test_fiscal_document_nfse_common import (
    TestFiscalDocumentNFSeCommon,
)

from ... import l10n_br_nfse_barueri

_logger = logging.getLogger(__name__)


class TestFiscalDocumentNFSeBarueri(TestFiscalDocumentNFSeCommon):
    def setUp(self):
        super().setUp()
        self.company.provedor_nfse = "barueri"

    def test_nfse_barueri_xml_esperado(self):
        """Garante que o XML gerado para Barueri permaneça compatível com o esperado."""

        xml_path = os.path.join(
            l10n_br_nfse_barueri.__path__[0], "tests", "nfse", "nfse.xml"
        )

        self.nfse_same_state.rps_number = "50"
        self.nfse_same_state.document_number = "50"

        with patch(
            "odoo.addons.l10n_br_nfse.models.document.Document.make_pdf",
            return_value=None,
        ):
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

        # Espera-se no máximo pequenas diferenças irrelevantes
        assert len(diff) <= 1

    def test_is_nfse_barueri_flag(self):
        """Valida o cálculo do campo técnico is_nfse_barueri."""
        barueri_city = self.env.ref("l10n_br_base.city_3505708")
        other_city = self.env.ref("l10n_br_base.city_3132404")

        self.company.city_id = barueri_city
        self.nfse_same_state.document_type = "SE"

        self.assertTrue(
            self.nfse_same_state.is_nfse_barueri,
        )

        self.company.city_id = other_city
        self.nfse_same_state.invalidate_cache(fnames=["is_nfse_barueri"])
        self.assertFalse(
            self.nfse_same_state.is_nfse_barueri,
        )

    def test_compute_url_nfse_barueri_ambientes(self):
        """Testa a geração da URL de consulta da
        NFSe em ambiente produção e homologação."""
        barueri_city = self.env.ref("l10n_br_base.city_3505708")
        self.company.city_id = barueri_city
        self.nfse_same_state.document_type = "SE"
        self.nfse_same_state.partner_id.cnpj_cpf = "12.345.678/0001-95"
        self.nfse_same_state.verify_code = "ABC123"

        self.nfse_same_state.nfse_environment = "1"
        self.nfse_same_state._compute_url_nfse_barueri()

        self.assertEqual(
            self.nfse_same_state.url_nfse_barueri,
            "https://www.barueri.sp.gov.br/nfe/wfimagemNota.aspx"
            "?CODIGOAUTENTICIDADE=ABC123&NUMDOC=12345678000195",
        )

        self.nfse_same_state.nfse_environment = "2"
        self.nfse_same_state._compute_url_nfse_barueri()

        self.assertEqual(
            self.nfse_same_state.url_nfse_barueri,
            "https://testeeiss.barueri.sp.gov.br/nfe/wfimagemNota.aspx"
            "?CODIGOAUTENTICIDADE=ABC123&NUMDOC=12345678000195",
        )

    def test_action_open_nfse_barueri(self):
        """Garante que a ação de abrir a NFSe retorna um ir.actions.act_url válido."""
        barueri_city = self.env.ref("l10n_br_base.city_3505708")
        self.company.city_id = barueri_city
        self.nfse_same_state.document_type = "SE"
        self.nfse_same_state.partner_id.cnpj_cpf = "12345678000195"
        self.nfse_same_state.verify_code = "COD123"
        self.nfse_same_state.nfse_environment = "1"
        self.nfse_same_state._compute_url_nfse_barueri()

        action = self.nfse_same_state.action_open_nfse_barueri()

        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertEqual(action["url"], self.nfse_same_state.url_nfse_barueri)
        self.assertEqual(action["target"], "new")

    def test_serialize_barueri_lote_rps_retorna_bytes(self):
        """Verifica que o lote RPS gerado para
        Barueri é retornado em bytes e não vazio."""
        barueri_city = self.env.ref("l10n_br_base.city_3505708")
        self.company.city_id = barueri_city
        self.nfse_same_state.document_type = "SE"

        now = datetime.now()
        self.nfse_same_state.document_date = now
        self.nfse_same_state.date_in_out = now

        rps_bytes = self.nfse_same_state._serialize_barueri_lote_rps()

        self.assertIsInstance(rps_bytes, (bytes, bytearray))
        self.assertTrue(rps_bytes, "O conteúdo do RPS não deveria ser vazio.")

    def test_baixar_xml_nfse_monta_url_corretamente(self):
        """Garante que o método de download de
        XML monta a URL esperada e trata o retorno."""
        autenticidade = "ABC123"
        cnpj = "12345678000195"

        with patch(
            "odoo.addons.l10n_br_nfse_barueri.models.document.requests.get"
        ) as mock_get:
            mock_response = MagicMock()
            mock_response.text = "<xml/>"
            mock_get.return_value = mock_response

            result = self.nfse_same_state._baixar_xml_nfse(autenticidade, cnpj)

        mock_get.assert_called_once()
        called_url = mock_get.call_args[0][0]
        self.assertIn("codigoautenticidade=ABC123", called_url)
        self.assertIn("numdoc=12345678000195", called_url)
        mock_response.raise_for_status.assert_called_once()
        self.assertEqual(result, "<xml/>")
