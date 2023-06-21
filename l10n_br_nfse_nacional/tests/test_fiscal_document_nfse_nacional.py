# Copyright (C) 2023 - TODAY Raphaël Valyi - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import gzip
import logging
import os
from datetime import datetime
from unittest import mock

from xmldiff import main

from odoo.tools import config

from odoo.addons.l10n_br_nfse.tests.test_fiscal_document_nfse_common import (
    TestFiscalDocumentNFSeCommon,
)

from ... import l10n_br_nfse_nacional

_logger = logging.getLogger(__name__)


FAKE_NFSE = """<?xml version="1.0" encoding="utf-8"?>
<NFSe versao="1.00" xmlns="http://www.sped.fazenda.gov.br/nfse">
    <infNFSe Id="NFS14001591201761135000132000000000000022097781063609">
    </infNFSe>
    <Signature xmlns="http://www.w3.org/2000/09/xmldsig#" />
</NFSe>
"""

compressed_nfse = gzip.compress(FAKE_NFSE.encode())
encoded_nfse = base64.b64encode(compressed_nfse).decode()


def mocked_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code
            self.text = str(json_data)

        def ok(self):
            return True

        def json(self):
            return self.json_data

    if args[0].endswith("/nfse"):
        return MockResponse(
            {
                "tipoAmbiente": 2,
                "versaoAplicativo": "42",
                "dataHoraProcessamento": "2020-07-30T17:28:42.584Z",
                "idDps": "123456",
                "chaveAcesso": "blabla",
                "nfseXmlGZipB64": encoded_nfse,
                "alertas": [
                    {
                        "mensagem": "string",
                        "parametros": ["string"],
                        "codigo": "codigo",
                        "descricao": "descriçao",
                        "complemento": "complemento",
                    }
                ],
            },
            201,
        )


class TestFiscalDocumentNFSeNacional(TestFiscalDocumentNFSeCommon):
    def setUp(self):
        super(TestFiscalDocumentNFSeNacional, self).setUp()
        self.company.provedor_nfse = "nacional"

    @mock.patch("requests.post", side_effect=mocked_requests_post)
    def test_nfse_nacional(self, mocked_requests_post):
        """Test NFS-e same state."""

        xml_path = os.path.join(
            l10n_br_nfse_nacional.__path__[0], "tests", "nfse", "nacional.xml"
        )

        self.nfse_same_state._onchange_document_serie_id()
        self.nfse_same_state._onchange_fiscal_operation_id()
        self.nfse_same_state._onchange_company_id()
        self.nfse_same_state.rps_number = "50"
        self.nfse_same_state.document_number = "50"

        for line in self.nfse_same_state.fiscal_line_ids:
            line._onchange_product_id_fiscal()
            line._onchange_commercial_quantity()
            line._onchange_ncm_id()
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_operation_line_id()
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
        _logger.info("XML file saved at %s" % (output,))

        diff = main.diff_files(xml_path, output)
        _logger.info("Diff with expected XML (if any): %s" % (diff,))

        assert len(diff) == 0

        # TODO mock and test
        self.nfse_same_state.action_document_send()
        # self.nfse_same_state.cancel_document_nacional()
