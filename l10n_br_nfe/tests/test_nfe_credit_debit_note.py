# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    EDOC_REFUND_CREDIT_TYPE,
    EDOC_REFUND_DEBIT_TYPE,
)
from odoo.addons.l10n_br_nfe_spec.models.v4_0.leiaute_nfe_v4_00 import (
    TTPNFCREDITO,
    TTPNFDEBITO,
)

ORIGINAL_KEY = "35260665910976000147550010000000011000000016"


@tagged("post_install", "-at_install")
class TestNFeCreditDebitNote(TransactionCase):
    """Credit and debit notes of the NF-e (NT 2025.002)"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.ref("base.main_company")
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
                "is_company": True,
                "cnpj_cpf": "65910976000147",
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "default_code": "TEST001", "list_price": 100.0}
        )
        operation = cls.env["l10n_br_fiscal.operation"]
        cls.op_credit = operation.create(
            {
                "code": "NC",
                "name": "Nota de Crédito",
                "fiscal_operation_type": "in",
                "edoc_purpose": "5",
            }
        )
        cls.op_debit = operation.create(
            {
                "code": "ND",
                "name": "Nota de Débito",
                "fiscal_operation_type": "out",
                "edoc_purpose": "6",
            }
        )
        cls.nfe = cls.env.ref("l10n_br_fiscal.document_55")
        cls.nfce = cls.env.ref("l10n_br_fiscal.document_65")
        cls.icms_cst_00 = cls.env.ref("l10n_br_fiscal.cst_icms_00")

    def _classification(self, code):
        return self.env.ref(f"l10n_br_fiscal.tax_classification_{code}")

    def _create_note(self, operation, note_type, code="000001", references=1):
        vals = {
            "company_id": self.company.id,
            "partner_id": self.partner.id,
            "fiscal_operation_id": operation.id,
            "fiscal_operation_type": operation.fiscal_operation_type,
            "document_type_id": self.nfe.id,
            "document_related_ids": [
                (
                    0,
                    0,
                    {
                        "document_type_id": self.nfe.id,
                        "document_key": ORIGINAL_KEY,
                    },
                )
                for __ in range(references)
            ],
        }
        if operation.edoc_purpose == "5":
            vals["edoc_refund_credit_type"] = note_type
        elif operation.edoc_purpose == "6":
            vals["edoc_refund_debit_type"] = note_type
        document = self.env["l10n_br_fiscal.document"].create(vals)
        self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": document.id,
                "name": "Item",
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 100.0,
                "tax_classification_id": self._classification(code).id,
            }
        )
        return document

    def assertNoteError(self, document, message):
        with self.assertRaisesRegex(UserError, message):
            document._check_nfe_credit_debit_note()

    def test_note_types_are_the_schema_types(self):
        """The credit and debit note types are the ones of the NF-e schema."""
        self.assertEqual(
            [code for code, __ in EDOC_REFUND_CREDIT_TYPE],
            [code for code, __ in TTPNFCREDITO],
        )
        self.assertEqual(
            [code for code, __ in EDOC_REFUND_DEBIT_TYPE],
            [code for code, __ in TTPNFDEBITO],
        )

    def test_note_type_follows_the_purpose(self):
        """The note type is cleared when the document is no longer a note."""
        document = self._create_note(self.op_credit, "04")
        self.assertEqual(document.edoc_purpose, "5")
        self.assertEqual(document.edoc_refund_credit_type, "04")

        document.fiscal_operation_id = self.op_debit
        self.assertEqual(document.edoc_purpose, "6")
        self.assertFalse(document.edoc_refund_credit_type)

        document.edoc_refund_debit_type = "04"
        document.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_venda")
        self.assertFalse(document.edoc_refund_debit_type)

    def test_credit_note_reduction(self):
        """A credit note of value reduction references the original NF-e."""
        document = self._create_note(self.op_credit, "04")
        document._check_nfe_credit_debit_note()
        document._document_check()

    def test_note_type_is_required(self):
        document = self._create_note(self.op_credit, False)
        self.assertNoteError(document, "Set the credit note type")
        document = self._create_note(self.op_debit, False, references=0)
        self.assertNoteError(document, "Set the debit note type")

    def test_note_issued_by_the_partner(self):
        """A note issued by the partner is not checked, the SEFAZ did."""
        document = self._create_note(self.op_credit, False)
        document.issuer = "partner"
        document._check_nfe_credit_debit_note()

    def test_note_type_only_in_notes(self):
        document = self._create_note(self.op_credit, "04")
        document.write({"edoc_purpose": "1", "edoc_refund_credit_type": "04"})
        self.assertNoteError(document, "Only a credit note can have")

    def test_note_operation_type(self):
        """A credit note is an incoming NF-e, a debit note an outgoing one."""
        document = self._create_note(self.op_credit, "04")
        document.fiscal_operation_type = "out"
        self.assertNoteError(document, "must be an incoming NF-e")
        document = self._create_note(self.op_debit, "04", references=0)
        document.fiscal_operation_type = "in"
        self.assertNoteError(document, "must be an outgoing NF-e")

    def test_note_model(self):
        document = self._create_note(self.op_credit, "04")
        document.document_type_id = self.nfce
        self.assertNoteError(document, "model 55")

    def test_credit_note_references(self):
        """Credit notes 01, 03 and 04 reference one NF-e, 02 none."""
        for credit_type in ("01", "03", "04"):
            self.assertNoteError(
                self._create_note(self.op_credit, credit_type, references=0),
                "must reference exactly one NF-e",
            )
            self.assertNoteError(
                self._create_note(self.op_credit, credit_type, references=2),
                "must reference exactly one NF-e",
            )
        document = self._create_note(self.op_credit, "02", code="810001")
        document.document_date = datetime(2029, 1, 2)
        self.assertNoteError(document, "cannot reference documents")
        document.document_related_ids = [(5, 0, 0)]
        document._check_nfe_credit_debit_note()

    def test_credit_note_reference_model(self):
        """Only a return credit note (03) can reference a NFC-e."""
        document = self._create_note(self.op_credit, "04")
        document.document_related_ids.document_type_id = self.nfce
        self.assertNoteError(document, "can only reference NF-e")
        document = self._create_note(self.op_credit, "03")
        document.document_related_ids.document_type_id = self.nfce
        document._check_nfe_credit_debit_note()

    def test_credit_note_zfm_from_2029(self):
        document = self._create_note(self.op_credit, "02", code="810001", references=0)
        document.document_date = datetime(2028, 12, 31)
        self.assertNoteError(document, "only be used from 2029")
        document.document_date = datetime(2029, 1, 1, 12)
        document._check_nfe_credit_debit_note()

    def test_note_type_classification(self):
        """Some note types require their cClassTrib (UB14-70 and UB14-80)."""
        document = self._create_note(self.op_debit, "08", references=0)
        self.assertNoteError(document, "the cClassTrib of this note type is 811003")
        document.fiscal_line_ids.tax_classification_id = self._classification("811003")
        document._check_nfe_credit_debit_note()

        document = self._create_note(self.op_credit, "05", references=0)
        self.assertNoteError(document, "the cClassTrib of this note type is 800001")

    def test_classification_only_in_its_note_types(self):
        """The cClassTrib of the note types is refused elsewhere (UB14-60)."""
        document = self._create_note(
            self.env.ref("l10n_br_fiscal.fo_venda"), False, code="811003"
        )
        self.assertNoteError(document, "the cClassTrib 811003 is only accepted in")
        # a type without required cClassTrib does not accept them either
        document = self._create_note(self.op_debit, "04", code="800001", references=0)
        self.assertNoteError(document, "the cClassTrib 800001 is only accepted in")
        # 800001 is the cClassTrib of the debit and of the credit notes 05
        for operation in (self.op_debit, self.op_credit):
            self._create_note(
                operation, "05", code="800001", references=0
            )._check_nfe_credit_debit_note()

    def test_note_only_ibs_cbs(self):
        """A note only informs IBS and CBS, except some types (B25-80)."""
        icms = self.env.ref("l10n_br_fiscal.tax_icms_12")
        ipi = self.env.ref("l10n_br_fiscal.tax_ipi_10")
        pis = self.env.ref("l10n_br_fiscal.tax_pis_0_65")

        document = self._create_note(self.op_debit, "04", references=0)
        document.fiscal_line_ids.fiscal_tax_ids = icms
        self.assertNoteError(document, "only informs IBS and CBS, remove ICMS")

        # exception 1: credit note of value reduction
        document = self._create_note(self.op_credit, "04")
        document.fiscal_line_ids.fiscal_tax_ids = icms | ipi | pis
        document._check_nfe_credit_debit_note()

        # exceptions 2 and 3: advance payment, IPI and, in 2026, PIS
        document = self._create_note(self.op_debit, "06", references=0)
        document.fiscal_line_ids.fiscal_tax_ids = ipi | pis
        document.document_date = datetime(2026, 11, 3, 12)
        document._check_nfe_credit_debit_note()
        document.document_date = datetime(2027, 1, 4, 12)
        self.assertNoteError(document, "remove PIS")

    def test_export_note_groups(self):
        """The XML of the note has the type and only the allowed taxes."""
        document = self._create_note(self.op_credit, "01")
        line = document.fiscal_line_ids
        line.write({"icms_cst_id": self.icms_cst_00.id, "cbs_value": 0.9})

        ide = document._build_binding(
            spec_schema="nfe", spec_version="40", class_name="nfe.40.ide"
        )
        self.assertEqual(ide.finNFe, "5")
        self.assertEqual(ide.tpNFCredito, "01")
        self.assertFalse(ide.tpNFDebito)
        self.assertEqual(ide.tpNF, "0")

        det = line._build_binding(
            spec_schema="nfe", spec_version="40", class_name="nfe.40.det"
        )
        for group in ("ICMS", "IPI", "II", "ISSQN", "PIS", "COFINS"):
            self.assertIsNone(getattr(det.imposto, group), group)
        self.assertEqual(det.imposto.IBSCBS.cClassTrib, "000001")

        # the credit note of value reduction keeps the other taxes
        document.edoc_refund_credit_type = "04"
        det = line._build_binding(
            spec_schema="nfe", spec_version="40", class_name="nfe.40.det"
        )
        self.assertIsNotNone(det.imposto.ICMS)
