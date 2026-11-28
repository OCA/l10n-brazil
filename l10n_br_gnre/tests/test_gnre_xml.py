# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from os import path

import nfelib
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
        # CNPJ inventado com digito verificador valido, e conferido para nao
        # colidir com nenhum parceiro de dados demo do repo: a suite completa
        # do CI instala todos os modulos com demo junto, e reusar um CNPJ real
        # (por exemplo o da KMEE em l10n_br_base_demo.xml) estoura a
        # constraint de unicidade de vat.
        cls.company.partner_id.write(
            {
                "vat": "99.001.100/2200-51",
                "l10n_br_ie_code": "633.606.400.022",
                "legal_name": "Empresa Emitente de Testes LTDA",
                "state_id": cls.env.ref("base.state_br_sp").id,
            }
        )
        cls.state_sp = cls.env.ref("base.state_br_sp")
        cls.state_rj = cls.env.ref("base.state_br_rj")
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

        # The official XSD ships with the nfelib bindings.
        cls.schema = etree.XMLSchema(
            etree.parse(
                path.join(
                    path.dirname(nfelib.__file__),
                    "gnre",
                    "schemas",
                    "v2_0",
                    "lote_gnre_v2.00.xsd",
                )
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

    def _create_guide(self, keys, fcp=0.0, config=None, partner=None):
        config = config or self.config
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
                    "partner_id": partner.id if partner else False,
                }
            )
            obligations |= self.env["l10n_br_gnre.obligation"].create(
                {
                    "company_id": self.company.id,
                    "document_id": document.id,
                    "config_id": config.id,
                    "fiscal_state_id": config.fiscal_state_id.id,
                    "tax_group_id": self.tax_group.id,
                    "revenue_code": config.revenue_code,
                    "amount_principal": 150.0,
                    "amount_fcp": fcp,
                    "period_ref": "072026",
                    "date_due": "2026-08-10",
                }
            )
        return self.env["l10n_br_fiscal.document"]._create_gnre_guide(obligations)

    def test_lote_validates_against_official_xsd(self):
        """O XML gerado passa no schema oficial v2.15."""
        guide = self._create_guide(["35260799001100220051550010000010001000010008"])
        lote = self.env["l10n_br_gnre.xml"].build_lote(guide)

        self.schema.assertValid(lote)

    def test_consolidated_lote_validates(self):
        """Guia com várias notas também passa no schema."""
        guide = self._create_guide(
            [
                "35260799001100220051550010000010001000010008",
                "35260799001100220051550010000010002000010006",
                "35260799001100220051550010000010003000010004",
            ]
        )
        lote = self.env["l10n_br_gnre.xml"].build_lote(guide)

        self.schema.assertValid(lote)
        itens = lote.findall(f".//{{{NS}}}item")
        self.assertEqual(len(itens), 3)

    def test_icms_and_fcp_share_the_same_item(self):
        """ICMS e FCP são dois valor do mesmo item, não itens separados."""
        guide = self._create_guide(
            ["35260799001100220051550010000010001000010008"], fcp=20.0
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
            ["35260799001100220051550010000010001000010008"], fcp=20.0
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
            ["35260799001100220051550010000010001000010008"], fcp=20.0
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

    def _rj_config(self, **values):
        return self.env["l10n_br_gnre.state.config"].create(
            dict(
                {
                    "company_id": self.company.id,
                    "fiscal_state_id": self.state_rj.id,
                    "tax_group_id": self.tax_group.id,
                    "amount_source": "difal",
                    "revenue_code": "100102",
                    "mode": "document",
                },
                **values,
            )
        )

    def _emitter(self, lote):
        emitente = lote.find(f".//{{{NS}}}contribuinteEmitente")
        return {etree.QName(child).localname: child for child in emitente}

    def test_emitter_without_registration_sends_the_address(self):
        """Sem IE na UF favorecida, vão endereço, município, UF e CEP."""
        self.company.partner_id.write(
            {
                "street": "Rua de Testes, 100",
                "district": "Centro",
                "zip": "01001-000",
                "phone": "(11) 3622-0000",
                "city_id": self.env.ref("l10n_br_base.city_3550308").id,
            }
        )
        guide = self._create_guide(
            ["35260799001100220051550010000010001000010008"], config=self._rj_config()
        )
        lote = self.env["l10n_br_gnre.xml"].build_lote(guide)

        self.schema.assertValid(lote)
        emitter = self._emitter(lote)
        identification = emitter["identificacao"]
        self.assertIsNone(identification.find(f"{{{NS}}}IE"))
        self.assertTrue(emitter["endereco"].text.startswith("Rua de Testes"))
        self.assertEqual(emitter["municipio"].text, "50308")
        self.assertEqual(emitter["uf"].text, "SP")
        self.assertEqual(emitter["cep"].text, "01001000")
        self.assertEqual(emitter["telefone"].text, "1136220000")

    def test_emitter_registered_in_the_favoured_state(self):
        """Com IE de substituto na UF favorecida, vai essa IE e não o endereço."""
        self.company.partner_id.state_tax_number_ids = [
            (0, 0, {"state_id": self.state_rj.id, "l10n_br_ie_code": "81265690"})
        ]
        guide = self._create_guide(
            ["35260799001100220051550010000010001000010008"], config=self._rj_config()
        )
        lote = self.env["l10n_br_gnre.xml"].build_lote(guide)

        self.schema.assertValid(lote)
        emitter = self._emitter(lote)
        self.assertEqual(emitter["identificacao"].find(f"{{{NS}}}IE").text, "81265690")
        self.assertNotIn("endereco", emitter)

    def test_recipient_is_sent_when_the_state_requires_it(self):
        """DIFAL a consumidor final: o destinatário vai no item."""
        customer = self.env["res.partner"].create(
            {
                "name": "Consumidor Final de Testes",
                "vat": "529.982.247-25",
                "state_id": self.state_rj.id,
                "city_id": self.env.ref("l10n_br_base.city_3304557").id,
            }
        )
        guide = self._create_guide(
            ["35260799001100220051550010000010001000010008"],
            config=self._rj_config(recipient_required=True),
            partner=customer,
        )
        lote = self.env["l10n_br_gnre.xml"].build_lote(guide)

        self.schema.assertValid(lote)
        recipient = lote.find(f".//{{{NS}}}item/{{{NS}}}contribuinteDestinatario")
        self.assertEqual(recipient.find(f".//{{{NS}}}CPF").text, "52998224725")
        self.assertEqual(
            recipient.find(f"{{{NS}}}razaoSocial").text, "Consumidor Final de Testes"
        )
        self.assertEqual(recipient.find(f"{{{NS}}}municipio").text, "04557")

    def test_recipient_is_left_out_by_default(self):
        guide = self._create_guide(
            ["35260799001100220051550010000010001000010008"], config=self._rj_config()
        )
        lote = self.env["l10n_br_gnre.xml"].build_lote(guide)

        self.assertIsNone(lote.find(f".//{{{NS}}}contribuinteDestinatario"))
