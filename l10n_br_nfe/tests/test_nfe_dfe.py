# Copyright (C) 2023 - TODAY Felipe Zago - KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# pylint: disable=line-too-long

from unittest import mock

from nfelib.nfe.ws.edoc_legacy import DocumentoElectronicoAdapter

from odoo.tests.common import TransactionCase

from odoo.addons.l10n_br_fiscal_dfe.tests.test_dfe import mocked_post_success_single
from odoo.addons.l10n_br_fiscal_dfe.tests.test_mde import MDe


class TestNFeDFe(TransactionCase):
    def setUp(self):
        super().setUp()

        self.dfe_id = self.env["l10n_br_fiscal.dfe"].create(
            {"company_id": self.env.ref("l10n_br_base.empresa_lucro_presumido").id}
        )

    @mock.patch.object(
        DocumentoElectronicoAdapter,
        "_post",
        side_effect=mocked_post_success_single,
    )
    @mock.patch.object(MDe, "action_ciencia_emissao", return_value=None)
    def test_download_document_proc_nfe(self, _mock_post, _mock_ciencia):
        self.dfe_id.search_documents()

        self.dfe_id.download_documents()
