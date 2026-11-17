# @ 2020 KMEE - www.kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_br_base.tests.tools import load_fixture_files

from .tools import load_fiscal_fixture_files


class TestFiscalDocumentNFSe(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        load_fiscal_fixture_files(cls.env)
        load_fixture_files(
            cls.env, "l10n_br_fiscal", file_names=["fiscal_document_nfse_demo.xml"]
        )
        cls.nfse_same_state = cls.env.ref("l10n_br_fiscal.demo_nfse_same_state")

    def test_nfse_same_state(self):
        """Test NFSe same state."""
        for line in self.nfse_same_state.fiscal_line_ids:
            self.assertEqual(
                line.fiscal_operation_line_id.name,
                "Prestação de Serviço",
                "Error to mappping Prestação de Serviço"
                " for Venda de Serviço de Contribuinte Dentro do Estado.",
            )

            # Service Type
            self.assertEqual(
                line.service_type_id.code,
                "1.05",
                "Error to mapping Service Type Code 1.05"
                " for Venda de Serviço de Contribuinte Dentro do Estado.",
            )

            # ISSQN
            self.assertEqual(
                line.issqn_tax_id.name,
                "ISSQN 5%",
                "Error to mapping ICMS CST Tributada com permissão de crédito"
                " for Venda de Serviço de Contribuinte Dentro do Estado.",
            )

    def test_document_split(self):
        """One service per service document; a product document keys only its type."""
        document = self.nfse_same_state
        line = document.fiscal_line_ids[:1]
        key = line._get_document_split_key(document.document_type_id)
        same = line.copy({"name": "Same service"})
        self.assertEqual(same._get_document_split_key(document.document_type_id), key)
        document._check_document_split()

        nfe = self.env.ref("l10n_br_fiscal.document_55")
        self.assertEqual(line._get_document_split_key(nfe), (nfe.id,))

        same.service_type_id = self.env["l10n_br_fiscal.service.type"].search(
            [("id", "!=", line.service_type_id.id), ("internal_type", "=", "normal")],
            limit=1,
        )
        with self.assertRaises(UserError):
            document.action_document_confirm()
