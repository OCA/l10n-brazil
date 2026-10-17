# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

KEY_1 = "35200159594315000157550010000000032062777166"
KEY_2 = "35200159594315000157550010000000022062777169"
KEY_OTHER_ISSUER = "35200681583054000129550010000000012760018057"


@tagged("post_install", "-at_install")
class TestNFeDFeReferenciado(TransactionCase):
    """Test the item references (det/DFeReferenciado) of return NF-e
    (NT 2025.002, VC02-14)"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("base.main_company")
        cls.nfe_type = cls.env.ref("l10n_br_fiscal.document_55")
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
                "is_company": True,
                "cnpj_cpf": "65910976000147",
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "default_code": "TEST001"}
        )

    def _create_document(self, fiscal_operation):
        return self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.partner.id,
                "fiscal_operation_type": fiscal_operation.fiscal_operation_type,
                "fiscal_operation_id": fiscal_operation.id,
                "document_type_id": self.nfe_type.id,
            }
        )

    def _create_return(self):
        return self._create_document(
            self.env.ref("l10n_br_fiscal.fo_devolucao_compras")
        )

    def _add_related(self, document, key):
        return self.env["l10n_br_fiscal.document.related"].create(
            {
                "document_id": document.id,
                "document_type_id": self.nfe_type.id,
                "document_key": key,
            }
        )

    def _add_line(self, document, **extra_vals):
        vals = {
            "document_id": document.id,
            "product_id": self.product.id,
            "quantity": 1.0,
            "price_unit": 100.0,
        }
        vals.update(extra_vals)
        return self.env["l10n_br_fiscal.document.line"].create(vals)

    def _export_dfe_ref(self, line):
        return line.with_context(
            spec_schema="nfe", spec_version="40"
        )._export_m2o_via_tag_hooks("nfe40_DFeReferenciado", self.env["nfe.40.det"])

    def _export_nfref(self, document):
        return document.with_context(
            spec_schema="nfe", spec_version="40"
        )._export_one2many("nfe40_NFref", self.env["nfe.40.ide"])

    def test_export_single_related_document(self):
        """With one related document the line only sets the item number"""
        document = self._create_return()
        self._add_related(document, KEY_1)
        line = self._add_line(document, ref_document_item=3)

        dfe_ref = self._export_dfe_ref(line)
        self.assertEqual(dfe_ref.chaveAcesso, KEY_1)
        self.assertEqual(dfe_ref.nItem, "3")

    def test_export_line_related_document(self):
        """With several related documents the line chooses one"""
        document = self._create_return()
        self._add_related(document, KEY_1)
        related_2 = self._add_related(document, KEY_2)
        line = self._add_line(
            document, ref_document_related_id=related_2.id, ref_document_item=1
        )

        dfe_ref = self._export_dfe_ref(line)
        self.assertEqual(dfe_ref.chaveAcesso, KEY_2)
        self.assertEqual(dfe_ref.nItem, "1")

    def test_export_ambiguous_related_document(self):
        """Several related documents and none chosen: no group exported"""
        document = self._create_return()
        self._add_related(document, KEY_1)
        self._add_related(document, KEY_2)
        line = self._add_line(document, ref_document_item=1)

        self.assertFalse(self._export_dfe_ref(line))

    def test_export_not_return(self):
        """Other purposes keep NFref and never export the group"""
        document = self._create_document(self.env.ref("l10n_br_fiscal.fo_venda"))
        self._add_related(document, KEY_1)
        line = self._add_line(document, ref_document_item=3)

        self.assertFalse(self._export_dfe_ref(line))
        self.assertEqual(len(self._export_nfref(document)), 1)

    def test_export_return_without_nfref(self):
        """Return NF-e does not export NFref (VC02-05)"""
        document = self._create_return()
        self._add_related(document, KEY_1)
        self._add_line(document, ref_document_item=3)

        self.assertEqual(self._export_nfref(document), [])
        self.assertTrue(document.document_related_ids)

    def test_check_valid_references(self):
        document = self._create_return()
        self._add_related(document, KEY_1)
        related_2 = self._add_related(document, KEY_2)
        related_1 = document.document_related_ids - related_2
        self._add_line(
            document, ref_document_related_id=related_1.id, ref_document_item=1
        )
        self._add_line(
            document, ref_document_related_id=related_2.id, ref_document_item=1
        )

        document._check_nfe_item_references()

    def test_check_missing_item(self):
        document = self._create_return()
        self._add_related(document, KEY_1)
        self._add_line(document)

        with self.assertRaisesRegex(UserError, "referenced item number"):
            document._check_nfe_item_references()

    def test_check_missing_related_document(self):
        document = self._create_return()
        self._add_line(document, ref_document_item=1)

        with self.assertRaisesRegex(UserError, "set the referenced document"):
            document._check_nfe_item_references()

    def test_check_duplicated_reference(self):
        document = self._create_return()
        self._add_related(document, KEY_1)
        self._add_line(document, ref_document_item=2)
        self._add_line(document, ref_document_item=2)

        with self.assertRaisesRegex(UserError, "already referenced"):
            document._check_nfe_item_references()

    def test_check_different_issuers(self):
        document = self._create_return()
        related_1 = self._add_related(document, KEY_1)
        related_2 = self._add_related(document, KEY_OTHER_ISSUER)
        self._add_line(
            document, ref_document_related_id=related_1.id, ref_document_item=1
        )
        self._add_line(
            document, ref_document_related_id=related_2.id, ref_document_item=1
        )

        with self.assertRaisesRegex(UserError, "same issuer"):
            document._check_nfe_item_references()

    def test_check_not_return(self):
        """Other purposes are not checked"""
        document = self._create_document(self.env.ref("l10n_br_fiscal.fo_venda"))
        self._add_line(document)

        document._check_nfe_item_references()
