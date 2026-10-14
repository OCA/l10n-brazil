# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestNFeIBSCBSGroups(TransactionCase):
    """IBSCBS groups by CST: credit transfer, period adjustment and credit
    reversal (NT 2025.002, IT 2025.002 v1.70)"""

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
        cls.op_debit = cls.env["l10n_br_fiscal.operation"].create(
            {
                "code": "ND",
                "name": "Nota de Débito",
                "fiscal_operation_type": "out",
                "edoc_purpose": "6",
            }
        )
        cls.document = cls.env["l10n_br_fiscal.document"].create(
            {
                "company_id": cls.company.id,
                "partner_id": cls.partner.id,
                "fiscal_operation_type": "out",
                "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
                "document_date": datetime(2026, 10, 13, 15, 0),
            }
        )

    def _create_line(self, code, document=None, **values):
        line = self.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": (document or self.document).id,
                "name": f"Item {code}",
                "product_id": self.product.id,
                "quantity": 1.0,
                "price_unit": 100.0,
                "tax_classification_id": self.env.ref(
                    f"l10n_br_fiscal.tax_classification_{code}"
                ).id,
            }
        )
        line.write(values)
        return line

    def _export_ibscbs(self, line):
        return line.with_context(
            spec_schema="nfe", spec_version="40"
        )._export_m2o_via_tag_hooks("nfe40_IBSCBS", self.env["nfe.40.imposto"])

    def test_credit_transfer(self):
        """CST 800 informs gTransfCred with the line values, the CST coming
        from the cClassTrib when the line has no IBS tax."""
        line = self._create_line("800002", ibs_value=10.0, cbs_value=90.0)

        result = self._export_ibscbs(line)

        self.assertEqual(result.CST, "800")
        self.assertEqual(result.cClassTrib, "800002")
        self.assertEqual(result.gTransfCred.vIBS, "10.00")
        self.assertEqual(result.gTransfCred.vCBS, "90.00")
        self.assertIsNone(result.gIBSCBS)
        self.assertIsNone(result.gAjusteCompet)

    def test_period_adjustment(self):
        """CST 811 informs gAjusteCompet in the period of the document."""
        line = self._create_line("811003", ibs_value=1.5, cbs_value=13.5)

        result = self._export_ibscbs(line)

        self.assertEqual(result.CST, "811")
        self.assertEqual(str(result.gAjusteCompet.competApur), "2026-10")
        self.assertEqual(result.gAjusteCompet.vIBS, "1.50")
        self.assertEqual(result.gAjusteCompet.vCBS, "13.50")
        self.assertIsNone(result.gIBSCBS)
        self.assertIsNone(result.gTransfCred)

    def test_credit_reversal(self):
        """A cClassTrib with credit reversal informs gEstornoCred, and CST
        410 informs no group of the choice."""
        line = self._create_line("410030", ibs_value=0.5, cbs_value=4.5)

        result = self._export_ibscbs(line)

        self.assertEqual(result.CST, "410")
        self.assertIsNone(result.gIBSCBS)
        self.assertEqual(result.gEstornoCred.vIBSEstCred, "0.50")
        self.assertEqual(result.gEstornoCred.vCBSEstCred, "4.50")

    def test_csts_without_group(self):
        """CSTs without ind_gIBSCBS (400, 410, 820) do not inform gIBSCBS,
        which the SEFAZ refuses (rule UB13-20)."""
        for code in ("400001", "410002", "820001"):
            result = self._export_ibscbs(self._create_line(code))
            self.assertEqual(result.CST, code[:3])
            self.assertIsNone(result.gIBSCBS, code)
            self.assertIsNone(result.gEstornoCred, code)

    def test_stock_loss_debit_note_reversal(self):
        """The stock loss debit note always informs gEstornoCred (UB116-20)."""
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.partner.id,
                "fiscal_operation_type": "out",
                "fiscal_operation_id": self.op_debit.id,
                "edoc_refund_debit_type": "07",
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
            }
        )
        line = self._create_line("410002", document=document)

        self.assertFalse(line.tax_classification_id.credit_reversal)
        result = self._export_ibscbs(line)
        self.assertEqual(result.gEstornoCred.vIBSEstCred, "0.00")

    def test_totals_by_group(self):
        """IBSCBSTot only adds up the items of gIBSCBS and totals the credit
        reversal (rules W59f-10 and W59g-10)."""
        self._create_line(
            "000001", ibs_base=1000.0, ibs_value=1.0, cbs_base=1000.0, cbs_value=9.0
        )
        self._create_line("800002", ibs_value=10.0, cbs_value=90.0)
        self._create_line("410030", ibs_value=0.5, cbs_value=4.5)

        self.assertEqual(self.document.nfe40_vBCIBSCBS, 1000.0)
        self.assertEqual(self.document.nfe40_vIBS, 1.0)
        self.assertEqual(self.document.nfe40_vCBS, 9.0)

        total = self.document._build_binding(
            spec_schema="nfe", spec_version="40", class_name="nfe.40.total"
        )
        self.assertEqual(total.IBSCBSTot.gIBS.vIBS, "1.00")
        self.assertEqual(total.IBSCBSTot.gCBS.vCBS, "9.00")
        self.assertEqual(total.IBSCBSTot.gEstornoCred.vIBSEstCred, "0.50")
        self.assertEqual(total.IBSCBSTot.gEstornoCred.vCBSEstCred, "4.50")
