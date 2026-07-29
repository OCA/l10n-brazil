# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from os import path

from lxml import etree

from odoo.tests import TransactionCase, tagged

NS = "http://www.gnre.pe.gov.br"


@tagged("post_install", "-at_install")
class TestGnreXml(TransactionCase):
    """Serialização do lote conforme o XSD 2.00.

    A prova de correção aqui é a validação contra o schema oficial do pacote do
    Manual de Integração v2.15, e não a comparação com uma string que eu mesmo
    escrevi. O XSD é a gramática autoritativa: se o XML passa nele, a SEFAZ não
    rejeita por forma.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.partner_id.write(
            {
                "cnpj_cpf": "23.130.935/0001-98",
                "inscr_est": "633.606.428.115",
                "legal_name": "Empresa Emitente de Testes LTDA",
            }
        )
        cls.state_sp = cls.env.ref("base.state_br_sp")
        cls.tax_group = cls.env.ref("l10n_br_fiscal.tax_group_icmsst")
        cls.document_type_nfe = cls.env["l10n_br_fiscal.document.type"].search(
            [("code", "=", "55")], limit=1
        )

        cls.config = cls.env["l10n_br_gnre.state.config"].create(
            {
                "company_id": cls.company.id,
                "fiscal_state_id": cls.state_sp.id,
                "tax_group_id": cls.tax_group.id,
                "revenue_code": "100099",
                "mode": "consolidated",
                "period": "0",
                "due_days": 10,
                "convenio": "CONV 001/26",
            }
        )

        cls.schema = etree.XMLSchema(
            etree.parse(
                path.join(path.dirname(__file__), "data", "lote_gnre_v2.00.xsd")
            )
        )

    def _as_tuples(self, node, depth=0):
        """Flatten the tree into (depth, tag, text, attrs) for comparison.

        Comparing the tree beats comparing serialized strings: it ignores
        indentation and namespace prefix choices, and points at the exact
        element when it fails.
        """
        text = (node.text or "").strip()
        rows = [(depth, etree.QName(node).localname, text, dict(node.attrib))]
        for child in node:
            if isinstance(child.tag, str):  # skip comments
                rows.extend(self._as_tuples(child, depth + 1))
        return rows

    def _create_guide(self, keys, fcp=0.0):
        obligations = self.env["l10n_br_gnre.obligation"]
        for index, key in enumerate(keys):
            document = self.env["l10n_br_fiscal.document"].create(
                {
                    "company_id": self.company.id,
                    "document_type_id": self.document_type_nfe.id,
                    "document_serie": "1",
                    "document_number": str(1000 + index),
                    "document_date": "2026-07-15",
                    "document_key": key,
                }
            )
            obligations |= self.env["l10n_br_gnre.obligation"].create(
                {
                    "company_id": self.company.id,
                    "document_id": document.id,
                    "config_id": self.config.id,
                    "fiscal_state_id": self.state_sp.id,
                    "tax_group_id": self.tax_group.id,
                    "revenue_code": self.config.revenue_code,
                    "amount_principal": 150.0,
                    "amount_fcp": fcp,
                    "period_ref": "072026",
                    "date_due": "2026-08-10",
                }
            )
        return self.env["l10n_br_fiscal.document"]._create_gnre_guide(obligations)

    def test_lote_validates_against_official_xsd(self):
        """O XML gerado passa no schema oficial v2.15."""
        guide = self._create_guide(["35260723130935000198550010000010001000010007"])
        lote = self.env["l10n_br_gnre.xml"].build_lote(guide)

        self.schema.assertValid(lote)

    def test_consolidated_lote_validates(self):
        """Guia com várias notas também passa no schema."""
        guide = self._create_guide(
            [
                "35260723130935000198550010000010001000010007",
                "35260723130935000198550010000010002000010005",
                "35260723130935000198550010000010003000010003",
            ]
        )
        lote = self.env["l10n_br_gnre.xml"].build_lote(guide)

        self.schema.assertValid(lote)
        itens = lote.findall(f".//{{{NS}}}item")
        self.assertEqual(len(itens), 3)

    def test_icms_and_fcp_share_the_same_item(self):
        """ICMS e FCP são dois valor do mesmo item, não itens separados."""
        guide = self._create_guide(
            ["35260723130935000198550010000010001000010007"], fcp=20.0
        )
        lote = self.env["l10n_br_gnre.xml"].build_lote(guide)

        self.schema.assertValid(lote)
        itens = lote.findall(f".//{{{NS}}}item")
        self.assertEqual(len(itens), 1, "um item, não dois")
        valores = itens[0].findall(f"{{{NS}}}valor")
        self.assertEqual(
            [(v.get("tipo"), v.text) for v in valores],
            [("11", "150.00"), ("12", "20.00")],
        )

    def test_lote_matches_reference_xml(self):
        """O XML sai exatamente como o layout descreve, elemento a elemento.

        A referência foi montada a partir do xs:sequence do XSD oficial e das
        descrições de campo do manual v2.15. Serve para travar a ordem e a
        formatação, que o schema sozinho não garante por inteiro.
        """
        guide = self._create_guide(
            ["35260723130935000198550010000010001000010007"], fcp=20.0
        )
        generated = self.env["l10n_br_gnre.xml"].render_lote(guide)

        with open(
            path.join(path.dirname(__file__), "data", "lote_gnre_esperado.xml"),
            encoding="utf-8",
        ) as reference_file:
            expected = reference_file.read()

        self.assertEqual(
            self._as_tuples(etree.fromstring(generated.encode())),
            self._as_tuples(etree.fromstring(expected.encode())),
        )

    def test_element_order_follows_the_schema(self):
        """A ordem dos elementos do item segue o xs:sequence do XSD."""
        guide = self._create_guide(
            ["35260723130935000198550010000010001000010007"], fcp=20.0
        )
        lote = self.env["l10n_br_gnre.xml"].build_lote(guide)

        item = lote.find(f".//{{{NS}}}item")
        tags = [etree.QName(child).localname for child in item]
        self.assertEqual(
            tags,
            [
                "receita",
                "documentoOrigem",
                "referencia",
                "dataVencimento",
                "valor",
                "valor",
                "convenio",
            ],
        )

    def test_guide_without_obligations_is_refused(self):
        """Guia vazia não vira XML silenciosamente."""
        from odoo.exceptions import UserError

        empty = self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company.id,
                "document_type_id": self.env["l10n_br_fiscal.document.type"]
                .search([("code", "=", "23")], limit=1)
                .id,
                "document_date": "2026-07-15",
            }
        )
        with self.assertRaises(UserError):
            self.env["l10n_br_gnre.xml"].build_lote(empty)
