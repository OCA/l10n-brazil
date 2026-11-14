# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

NS = {"nfe": "http://www.portalfiscal.inf.br/nfe"}


@tagged("post_install", "-at_install")
class TestNFeIntermediary(TransactionCase):
    """indIntermed and infIntermed (NT 2020.006)"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.partner = cls.env["res.partner"].create(
            {"name": "Buyer", "cnpj_cpf": "65910976000147", "is_company": True}
        )
        cls.intermediary = cls.env["res.partner"].create(
            {
                "name": "Marketplace",
                "cnpj_cpf": "11.222.333/0001-81",
                "is_company": True,
            }
        )
        cls.document = cls.env["l10n_br_fiscal.document"].create(
            {
                "company_id": cls.env.ref("base.main_company").id,
                "partner_id": cls.partner.id,
                "fiscal_operation_type": "out",
                "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
                "ind_pres": "2",
            }
        )

    def _export(self):
        return self.document.with_context(
            spec_schema="nfe", spec_version="40"
        )._export_m2o_via_tag_hooks("nfe40_infIntermed", self.env["nfe.40.infnfe"])

    def _export_through_document(self, document=None):
        document = document or self.document
        return document.with_context(
            spec_schema="nfe", spec_version="40"
        )._export_many2one("nfe40_infIntermed", False, self.env["nfe.40.infnfe"])

    def _set_intermediary(self, code="LOJA_TESTE", **values):
        self.document.write(
            dict(
                intermediary_partner_id=self.intermediary.id,
                intermediary_seller_code=code,
                **values,
            )
        )

    def test_own_site_sale(self):
        self.assertEqual(self.document.nfe40_indIntermed, "0")
        self.assertFalse(self._export())
        self.assertFalse(self._export_through_document())

    def test_marketplace_sale(self):
        self._set_intermediary()
        self.assertEqual(self.document.nfe40_indIntermed, "1")
        result = self._export_through_document()
        self.assertEqual(result.CNPJ, "11222333000181")
        self.assertEqual(result.idCadIntTran, "LOJA_TESTE")

    def test_presential_sale_with_intermediary(self):
        self._set_intermediary(ind_pres="1")
        self.assertEqual(self.document.nfe40_indIntermed, "1")
        self.assertEqual(self._export().idCadIntTran, "LOJA_TESTE")

    def test_presential_sale_without_intermediary(self):
        self.document.ind_pres = "1"
        self.assertFalse(self.document.nfe40_indIntermed)
        self.assertFalse(self._export_through_document())

    def test_intermediary_forbidden_by_presence(self):
        self._set_intermediary()
        for ind_pres in ("0", "5"):
            with self.subTest(ind_pres=ind_pres):
                self.document.ind_pres = ind_pres
                self.assertFalse(self.document.nfe40_indIntermed)
                with self.assertRaisesRegex(UserError, "B25c-20"):
                    self._export_through_document()

    def test_delivery_nfce(self):
        self._set_intermediary(
            code="merchant-1",
            document_type_id=self.env.ref("l10n_br_fiscal.document_65").id,
            ind_pres="4",
        )
        self.assertEqual(self.document.nfe40_indIntermed, "1")
        self.assertEqual(self._export().idCadIntTran, "merchant-1")

    def test_seller_code_required_and_normalized(self):
        self._set_intermediary(code=False)
        with self.assertRaisesRegex(UserError, "seller id"):
            self._export()
        for code in ("A", "X" * 61):
            with self.subTest(code=code):
                self.document.intermediary_seller_code = code
                with self.assertRaisesRegex(UserError, "2 to 60 characters"):
                    self._export()
        self.document.intermediary_seller_code = " LOJA "
        self.assertEqual(self._export().idCadIntTran, "LOJA")

    def test_intermediary_needs_a_valid_cnpj(self):
        person = self.env["res.partner"].create(
            {
                "name": "Natural person",
                "cnpj_cpf": "529.982.247-25",
                "country_id": self.env.ref("base.br").id,
            }
        )
        self._set_intermediary()
        self.document.intermediary_partner_id = person
        with self.assertRaisesRegex(UserError, "valid CNPJ"):
            self._export()
        self.document.intermediary_partner_id = self.intermediary
        self.intermediary.cnpj_cpf = False
        with self.assertRaisesRegex(UserError, "valid CNPJ"):
            self._export()

    def test_intermediary_is_the_issuer(self):
        self._set_intermediary()
        self.document.intermediary_partner_id = self.document.company_id.partner_id
        with self.assertRaisesRegex(UserError, "issuer CNPJ"):
            self._export()

    def test_imported_infintermed_record(self):
        imported = self.env["nfe.40.infintermed"].create(
            {"nfe40_CNPJ": "11222333000181", "nfe40_idCadIntTran": "IMPORTED"}
        )
        self.document.nfe40_infIntermed = imported
        self.assertEqual(self.document.nfe40_indIntermed, "1")
        self.assertEqual(self._export_through_document().idCadIntTran, "IMPORTED")
        self._set_intermediary()
        self.assertEqual(self._export_through_document().idCadIntTran, "LOJA_TESTE")

    def test_serialized_xml(self):
        """The group and the indicator reach the XML sent to SEFAZ."""
        nfe = self.env.ref("l10n_br_nfe.demo_nfe_natural_icms_7_resale")
        nfe.write(
            {
                "ind_pres": "2",
                "intermediary_partner_id": self.intermediary.id,
                "intermediary_seller_code": "LOJA_TESTE",
            }
        )
        root = etree.fromstring(nfe.serialize()[0].to_xml().encode())
        inf_nfe = "nfe:infNFe"
        self.assertEqual(
            root.findtext(f"{inf_nfe}/nfe:ide/nfe:indIntermed", namespaces=NS), "1"
        )
        self.assertEqual(
            root.findtext(f"{inf_nfe}/nfe:infIntermed/nfe:CNPJ", namespaces=NS),
            "11222333000181",
        )
        self.assertEqual(
            root.findtext(f"{inf_nfe}/nfe:infIntermed/nfe:idCadIntTran", namespaces=NS),
            "LOJA_TESTE",
        )
        nfe.intermediary_partner_id = False
        root = etree.fromstring(nfe.serialize()[0].to_xml().encode())
        self.assertEqual(
            root.findtext(f"{inf_nfe}/nfe:ide/nfe:indIntermed", namespaces=NS), "0"
        )
        self.assertIsNone(root.find(f"{inf_nfe}/nfe:infIntermed", NS))
