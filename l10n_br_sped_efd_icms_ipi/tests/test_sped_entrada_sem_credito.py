# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

from odoo.tests.common import tagged

from odoo.addons.l10n_br_tax_assessment.tests.common_entrada import SpedEntradaCommon

from .test_sped_entrada import EntradaHelpers


@tagged("post_install", "-at_install")
class TestSpedEfdIcmsIpiEntradaSemCredito(EntradaHelpers, SpedEntradaCommon):
    """An entry without credit right: the CFOP of use and consumption or of the
    fixed asset vetoes the credit, and the books carry the tax out."""

    def setUp(self):
        super().setUp()
        self._opt_in()

    @staticmethod
    def _line(move):
        return move.fiscal_document_id.fiscal_line_ids

    def _by_cfop(self, declaration, register):
        return {rec["CFOP"]: rec for rec in self._sped_records(declaration, register)}

    def _assess_ipi_of_july(self):
        """Without a posted IPI assessment the E500 tree stays out of the file."""
        group = self.env["account.tax.group"].search(
            [
                (
                    "fiscal_tax_group_id",
                    "=",
                    self.env.ref("l10n_br_fiscal.tax_group_ipi").id,
                )
            ],
            limit=1,
        )
        accounts = {
            "property_tax_payable_account_id": ("IPIPAY", "liability_current"),
            "property_tax_receivable_account_id": ("IPIREC", "asset_current"),
        }
        group.with_company(self.company).write(
            {
                field: self.env["account.account"]
                .create(
                    {
                        "name": code,
                        "code": code,
                        "account_type": account_type,
                        "company_id": self.company.id,
                    }
                )
                .id
                for field, (code, account_type) in accounts.items()
            }
        )
        assessment = self.env["l10n_br_tax.assessment"].create(
            {
                "company_id": self.company.id,
                "tax_group_id": group.id,
                "date_from": "2026-07-01",
                "date_to": "2026-07-31",
            }
        )
        assessment.action_compute()
        assessment.action_post()
        return assessment

    def test_the_entry_without_credit_carries_no_icms(self):
        """Use and consumption and fixed asset: CST of the origin plus 90 and no
        base, rate or value of ICMS in the C170, the C190 and the C100. The
        resale keeps its credit."""
        resale = self._purchase_move("fo_compras_compras_comercializacao", "602")
        consumption = self._purchase_move("fo_compras_compras_uso_consumo", "603")
        asset = self._purchase_move("fo_compras_compras_ativo", "604")
        restricted = {consumption: "purchase_ownuse", asset: "purchase_asset"}
        for move, type_move in restricted.items():
            line = self._line(move)
            self.assertEqual(line.cfop_id.type_move, type_move)
            self.assertGreater(line.icms_value, 0, "the note has ICMS")
            self.assertTrue(line.icms_cst_id.default_creditable_tax)
            self.assertEqual(line._get_tax_creditability_map()["icms"], "cost")
        declaration = self._declaration_july()
        c100 = self._c100(declaration)
        resale_doc = resale.fiscal_document_id
        self.assertGreater(resale_doc.amount_icms_value, 0)
        self.assertAlmostEqual(
            self._number(c100[resale_doc.document_number]["VL_ICMS"]),
            resale_doc.amount_icms_value,
        )
        c170 = self._by_cfop(declaration, "C170")
        c190 = self._by_cfop(declaration, "C190")
        for move in restricted:
            number = move.fiscal_document_id.document_number
            self.assertEqual(self._number(c100[number]["VL_BC_ICMS"]), 0.0)
            self.assertEqual(self._number(c100[number]["VL_ICMS"]), 0.0)
            line = self._line(move)
            cfop = line.cfop_id.code
            for rec in (c170[cfop], c190[cfop]):
                self.assertEqual(rec["CST_ICMS"], f"{line.icms_origin or '0'}90")
                for name in ("VL_BC_ICMS", "ALIQ_ICMS", "VL_ICMS"):
                    self.assertEqual(self._number(rec[name]), 0.0, name)
            self.assertAlmostEqual(
                self._number(c190[cfop]["VL_OPR"]), line.fiscal_amount_total
            )
        resale_cfop = self._line(resale).cfop_id.code
        self.assertGreater(self._number(c190[resale_cfop]["VL_ICMS"]), 0)
        self.assertFalse(c190[resale_cfop]["CST_ICMS"].endswith("90"))

    def test_an_entry_whose_cst_gives_no_credit_keeps_it(self):
        """The map says cost for an exempt use and consumption (ICMS 40) too,
        but the CST already says there is no credit: the books keep 40. Only a
        CST that credits by its nature turns into 90."""
        _doc, exempt = self._entry_document(
            operation_line="fo_compras_compras_uso_consumo",
            line_vals={
                "icms_cst_id": self.env.ref("l10n_br_fiscal.cst_icms_40").id,
                "icms_base": 0.0,
                "icms_percent": 0.0,
                "icms_value": 0.0,
            },
        )
        _doc, taxed = self._entry_document(
            operation_line="fo_compras_compras_uso_consumo"
        )
        self.assertEqual(exempt.cfop_id.type_move, "purchase_ownuse")
        self.assertEqual(exempt.icms_cst_id.code, "40")
        self.assertEqual(exempt._get_tax_creditability_map()["icms"], "cost")
        self.assertEqual(taxed.icms_value, 120.0)
        declaration = self._declaration_july()
        c170 = self._sped_records(declaration, "C170")
        self.assertEqual(sorted(rec["CST_ICMS"] for rec in c170), ["040", "090"])
        c190 = {rec["CST_ICMS"]: rec for rec in self._sped_records(declaration, "C190")}
        self.assertEqual(set(c190), {"040", "090"})
        self.assertEqual(self._number(c190["090"]["VL_ICMS"]), 0.0)
        self.assertEqual(self._number(c190["040"]["VL_ICMS"]), 0.0)

    def test_the_resale_of_the_presumed_profit_keeps_its_credit(self):
        """The resale the PVA validated in the presumed profit: ICMS and IPI
        with credit, as the document carries them."""
        self.assertEqual(self.company.profit_calculation, "presumed")
        move = self._purchase_move("fo_compras_compras_comercializacao", "621")
        document = move.fiscal_document_id
        line = self._line(move)
        self.assertGreater(line.icms_value, 0)
        self.assertGreater(line.ipi_value, 0)
        self.assertEqual(
            line._get_tax_creditability_map(),
            {"icms": "credit", "ipi": "credit", "pis": "cost", "cofins": "cost"},
        )
        declaration = self._declaration_july()
        c170 = self._c170(declaration)
        self.assertEqual(
            c170["CST_ICMS"], f"{line.icms_origin or '0'}{line.icms_cst_code}"
        )
        self.assertAlmostEqual(self._number(c170["VL_BC_ICMS"]), line.icms_base)
        self.assertAlmostEqual(self._number(c170["ALIQ_ICMS"]), line.icms_percent)
        self.assertAlmostEqual(self._number(c170["VL_ICMS"]), line.icms_value)
        self.assertEqual(c170["CST_IPI"], line.ipi_cst_id.code)
        self.assertAlmostEqual(self._number(c170["VL_IPI"]), line.ipi_value)
        c100 = self._c100(declaration)[document.document_number]
        self.assertAlmostEqual(
            self._number(c100["VL_BC_ICMS"]), document.amount_icms_base
        )
        self.assertAlmostEqual(
            self._number(c100["VL_ICMS"]), document.amount_icms_value
        )
        self.assertAlmostEqual(self._number(c100["VL_IPI"]), document.amount_ipi_value)
        c190 = self._sped_records(declaration, "C190")
        self.assertEqual(len(c190), 1)
        self.assertEqual(c190[0]["CST_ICMS"], c170["CST_ICMS"])
        self.assertAlmostEqual(self._number(c190[0]["VL_ICMS"]), line.icms_value)
        self.assertAlmostEqual(self._number(c190[0]["VL_IPI"]), line.ipi_value)

    def test_the_ipi_of_an_entry_without_credit_stays_out_of_the_books(self):
        """Use and consumption does not credit the IPI: the C170, the C190, the
        C100 and the E510 carry CST 49 and no IPI. The industrialization keeps
        it."""
        consumption = self._purchase_move("fo_compras_compras_uso_consumo", "611")
        industrialization = self._purchase_move("fo_compras_compras", "612")
        consumption_line = self._line(consumption)
        industry_line = self._line(industrialization)
        self.assertEqual(industry_line.cfop_id.type_move, "purchase_industry")
        self.assertGreater(consumption_line.ipi_value, 0, "the note has IPI")
        self.assertGreater(industry_line.ipi_value, 0)
        self.assertTrue(consumption_line.ipi_cst_id.default_creditable_tax)
        self.assertEqual(consumption_line._get_tax_creditability_map()["ipi"], "cost")
        self.assertEqual(industry_line._get_tax_creditability_map()["ipi"], "credit")
        self._assess_ipi_of_july()
        declaration = self._declaration_july()
        consumption_cfop = consumption_line.cfop_id.code
        industry_cfop = industry_line.cfop_id.code
        c170 = self._by_cfop(declaration, "C170")
        self.assertEqual(c170[consumption_cfop]["CST_IPI"], "49")
        for name in ("VL_BC_IPI", "ALIQ_IPI", "VL_IPI"):
            self.assertEqual(self._number(c170[consumption_cfop][name]), 0.0, name)
        self.assertAlmostEqual(
            self._number(c170[industry_cfop]["VL_IPI"]), industry_line.ipi_value
        )
        c190 = self._by_cfop(declaration, "C190")
        self.assertEqual(self._number(c190[consumption_cfop]["VL_IPI"]), 0.0)
        self.assertAlmostEqual(
            self._number(c190[industry_cfop]["VL_IPI"]), industry_line.ipi_value
        )
        c100 = self._c100(declaration)
        self.assertEqual(
            self._number(
                c100[consumption.fiscal_document_id.document_number]["VL_IPI"]
            ),
            0.0,
        )
        self.assertAlmostEqual(
            self._number(
                c100[industrialization.fiscal_document_id.document_number]["VL_IPI"]
            ),
            industry_line.ipi_value,
        )
        e510 = {
            (rec["CFOP"], rec["CST_IPI"]): rec
            for rec in self._sped_records(declaration, "E510")
        }
        without_credit = e510[(consumption_cfop, "49")]
        self.assertEqual(self._number(without_credit["VL_BC_IPI"]), 0.0)
        self.assertEqual(self._number(without_credit["VL_IPI"]), 0.0)
        self.assertAlmostEqual(
            self._number(without_credit["VL_CONT_IPI"]),
            consumption_line.fiscal_amount_total,
        )
        self.assertAlmostEqual(
            sum(self._number(rec["VL_IPI"]) for rec in e510.values()),
            industry_line.ipi_value,
        )
