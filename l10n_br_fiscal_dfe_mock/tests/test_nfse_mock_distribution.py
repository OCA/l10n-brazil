# Copyright 2026 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase

from odoo.addons.l10n_br_nfse_dfe.services.nfse_xml import (
    decode_arquivo_xml,
    parse_nfse_xml,
)


class TestNfseMockDistribution(TransactionCase):
    """The NFS-e side of the mock: the pool, the ADN answer and the inbox."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_simples_nacional")
        cls.company.sudo().write({"dfe_mock_mode": True})

    def setUp(self):
        super().setUp()
        self.env["dfe.mock.nsu"].sudo().search(
            [("company_id", "=", self.company.id)]
        ).unlink()

    def _generate(self, quantity=2):
        wizard = self.env["dfe.mock.generate.wizard"].create(
            {
                "company_id": self.company.id,
                "fiscal_type": "nfse",
                "quantity": quantity,
            }
        )
        wizard.action_generate()
        return self.env["dfe.mock.nsu"].search(
            [("company_id", "=", self.company.id), ("fiscal_type", "=", "nfse")],
            order="nsu asc",
        )

    def test_generated_pool_is_parsable(self):
        """Each generated row carries an NFS-e the importer can read."""
        records = self._generate()
        self.assertEqual(len(records), 2)
        for record in records:
            self.assertEqual(record.schema_type, "NFSe")
            self.assertEqual(len(record.access_key), 50)
            parsed = parse_nfse_xml(record.xml_content.encode())
            self.assertTrue(parsed, "the national NFS-e binding did not parse")
            self.assertEqual(parsed["access_key"], record.access_key)
            self.assertTrue(parsed["provider_cnpj"])
            self.assertGreater(parsed["service_value"], 0)

    def test_access_key_check_digit(self):
        """The 50th digit is the mod 11 of the other 49."""
        record = self._generate(quantity=1)
        key = record.access_key
        weights = [2, 3, 4, 5, 6, 7, 8, 9]
        total = sum(
            int(digit) * weights[idx % len(weights)]
            for idx, digit in enumerate(reversed(key[:-1]))
        )
        remainder = total % 11
        expected = "0" if remainder < 2 else str(11 - remainder)
        self.assertEqual(key[-1], expected)

    def test_consulta_dfe_answers_from_the_pool(self):
        """The ADN call is a cursor over the pool, and 404 once caught up."""
        records = self._generate(quantity=3)
        response = self.company._nfse_consulta_dfe(0)
        self.assertEqual(response.status_code, 200)
        items = response.body["LoteDFe"]
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0]["TipoDocumento"], "NFSE")
        self.assertEqual(items[0]["ChaveAcesso"], records[0].access_key)
        self.assertTrue(decode_arquivo_xml(items[0]["ArquivoXml"]).startswith(b"<?xml"))

        # The cursor skips what is behind it, and the feed ends with a 404.
        after_first = self.company._nfse_consulta_dfe(int(records[0].nsu))
        self.assertEqual(len(after_first.body["LoteDFe"]), 2)
        self.assertEqual(
            self.company._nfse_consulta_dfe(int(records[-1].nsu)).status_code, 404
        )

    def test_distribution_fills_the_inbox(self):
        """A full distribution run creates the DF-e documents offline."""
        records = self._generate(quantity=2)
        self.company.sudo().write({"nfse_last_nsu": "0", "nfse_dfe_next_query": False})
        self.company._nfse_document_distribution()
        documents = self.env["l10n_br_fiscal_dfe.document"].search(
            [("company_id", "=", self.company.id), ("fiscal_type", "=", "nfse")]
        )
        self.assertEqual(
            sorted(documents.mapped("access_key")),
            sorted(records.mapped("access_key")),
        )
        for document in documents:
            self.assertEqual(document.document_state, "1")
            self.assertTrue(document.emitter)
            self.assertGreater(document.document_amount, 0)

    def test_nfe_pool_is_not_served_to_nfse(self):
        """The two feeds are numbered and served apart."""
        self.env["dfe.mock.nsu"].create(
            {
                "nsu": "000000000000001",
                "fiscal_type": "nfe",
                "schema_type": "resNFe",
                "xml_content": "<resNFe/>",
                "company_id": self.company.id,
            }
        )
        self.assertEqual(self.company._nfse_consulta_dfe(0).status_code, 404)
        record = self._generate(quantity=1)
        # The NFS-e feed starts at 1 of its own, beside the NF-e row.
        self.assertEqual(record.nsu, "000000000000001")
