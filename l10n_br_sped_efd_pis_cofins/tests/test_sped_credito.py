# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

import calendar
from datetime import date, datetime

from odoo.exceptions import UserError
from odoo.tests.common import tagged

from odoo.addons.l10n_br_tax_assessment.tests.common_entrada import SpedEntradaCommon

from .test_sped_entrada import SpedPisCofinsEntradaMixin


class CreditMixin(SpedPisCofinsEntradaMixin):
    """Entries and a sale posted by the normal path, and the PIS/COFINS
    assessment of the month, for the EFD Contribuicoes."""

    @staticmethod
    def _number(text):
        return float(text.replace(",", ".") or 0)

    def _set_accountant(self):
        city = self.env["res.city"].search([("state_id.code", "=", "SP")], limit=1)
        self.company.accountant_id = self.env["res.partner"].create(
            {
                "name": "Accountant",
                "is_accountant": True,
                "cnpj_cpf": "111.444.777-35",
                "crc_code": "1SP123456/O-0",
                "email": "accountant@example.com",
                "country_id": self.env.ref("base.br").id,
                "state_id": self.env.ref("base.state_br_sp").id,
                "city_id": city.id,
            }
        )

    def _opt_in_entry_without_credit(self):
        """The company books the tax it may not credit in the cost: the ledger
        and the books leave use and consumption and fixed asset out of the
        credit."""
        if "stock_valuation_via_stock_price" not in self.company._fields:
            self.skipTest("l10n_br_stock_account is not installed")
        self.company.stock_valuation_via_stock_price = True
        self.assertTrue(self.company._books_entry_by_creditability())

    def _entry(self, operation_line, number, invoice_date=None):
        """A posted supplier bill whose fiscal document the import left."""
        bill = self._purchase_move(operation_line, number, invoice_date=invoice_date)
        bill.fiscal_document_id.imported_document = True
        return bill

    def _sale(self, day=date(2026, 7, 12)):
        ref = self.env.ref
        sale = self.init_invoice(
            "out_invoice",
            partner=self.partner_a,
            invoice_date=day,
            products=[self.product_a],
            document_type=ref("l10n_br_fiscal.document_55"),
            fiscal_operation=ref("l10n_br_fiscal.fo_venda"),
            fiscal_operation_lines=[ref("l10n_br_fiscal.fo_venda_venda")],
            document_serie_id=self.empresa_lc_document_55_serie_1,
        )
        sale.action_post()
        # the fiscal document of a posted sale takes the day of the posting
        when = datetime(day.year, day.month, day.day, 12, 0)
        self.env.cr.execute(
            "UPDATE l10n_br_fiscal_document SET document_date = %s, date_in_out = %s"
            " WHERE id = %s",
            (when, when, sale.fiscal_document_id.id),
        )
        sale.fiscal_document_id.invalidate_recordset(["document_date", "date_in_out"])
        number = sale.fiscal_document_id.document_number
        sale.fiscal_document_id.write(
            {
                "state_edoc": "autorizada",
                "document_key": self._access_key(str(number), "11222333000181"),
            }
        )
        return sale

    def _assess(self, tax_domain, regime="non_cumulative", month=7, post=True):
        """The assessment of the month by the normal path: compute from the
        ledger, post."""
        group = self.env["account.tax.group"].search(
            [
                (
                    "fiscal_tax_group_id",
                    "=",
                    self.env.ref(f"l10n_br_fiscal.tax_group_{tax_domain}").id,
                )
            ],
            limit=1,
        )
        if regime:
            group.regime = regime
        accounts = {
            "property_tax_payable_account_id": ("PAY", "liability_current"),
            "property_tax_receivable_account_id": ("REC", "asset_current"),
        }
        if not group.with_company(self.company).property_tax_payable_account_id:
            group.with_company(self.company).write(
                {
                    field: self.env["account.account"]
                    .create(
                        {
                            "name": f"{tax_domain} {code}",
                            "code": f"{tax_domain.upper()}{code}",
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
                "date_from": date(2026, month, 1),
                "date_to": date(2026, month, calendar.monthrange(2026, month)[1]),
            }
        )
        assessment.action_compute()
        if post:
            assessment.action_post()
        return assessment

    def _month_with_credit(self):
        """A resale and an industrialization (credit), a use and consumption and a
        fixed asset (no credit), and a sale."""
        self._entry("fo_compras_compras_comercializacao", "401")
        self._entry("fo_compras_compras", "402")
        self._entry("fo_compras_compras_uso_consumo", "403")
        self._entry("fo_compras_compras_ativo", "404")
        self._sale()
        return self._assess("pis"), self._assess("cofins")


@tagged("post_install", "-at_install")
class TestSpedPisCofinsCredit(CreditMixin, SpedEntradaCommon):
    """The PIS/COFINS credit of the non-cumulative regime in the EFD
    Contribuicoes of a Lucro Real company."""

    profit_calculation = "real"

    def setUp(self):
        super().setUp()
        self._opt_in_entry_without_credit()

    def test_the_company_of_the_fixture_pays_the_basic_rates(self):
        """The non-cumulative regime has PIS 1.65% and COFINS 7.6%: the
        fixture of the non-cumulative company does not use the cumulative
        0.65% and 3% of the shared common of the account tests."""
        bill = self._purchase_move("fo_compras_compras_comercializacao", "401")
        line = bill.fiscal_document_id.fiscal_line_ids
        self.assertAlmostEqual(line.pis_percent, 1.65)
        self.assertAlmostEqual(line.cofins_percent, 7.6)

    def test_use_consumption_and_asset_book_no_credit_in_the_c170(self):
        """The ledger credits PIS/COFINS only of a resale and of an input, so the
        C170 of a use and consumption and of a fixed asset is CST 70 with no
        value, not CST 50 with a credit the books do not have."""
        self._entry("fo_compras_compras_uso_consumo", "403")
        self._entry("fo_compras_compras_ativo", "404")
        for record in self._sped_records(self._declaration_july(), "C170"):
            self.assertEqual(record["CST_PIS"], "70")
            self.assertEqual(record["CST_COFINS"], "70")
            self.assertEqual(self._number(record["VL_PIS"]), 0.0)
            self.assertEqual(self._number(record["VL_COFINS"]), 0.0)

    def test_the_credit_blocks_follow_the_c170_of_the_entries(self):
        """M100 by type and rate, M105 by nature of the base: only the resale
        (01) and the input (02) give credit, as the C170 books."""
        self._month_with_credit()
        declaration = self._declaration_july()
        m100 = self._sped_records(declaration, "M100")
        m105 = self._sped_records(declaration, "M105")
        self.assertEqual(len(m100), 1)
        self.assertEqual(m100[0]["COD_CRED"], "101")
        self.assertEqual(m100[0]["IND_CRED_ORI"], "0")
        self.assertEqual(m100[0]["VL_BC_CRED"], "2000,00")
        self.assertEqual(m100[0]["ALIQ_PIS"], "1,65")
        self.assertEqual(m100[0]["VL_CRED"], "33,00")
        self.assertEqual(m100[0]["VL_CRED_DISP"], "33,00")
        self.assertEqual(
            sorted((rec["NAT_BC_CRED"], rec["CST_PIS"]) for rec in m105),
            [("01", "50"), ("02", "50")],
        )
        self.assertEqual(
            sum(self._number(rec["VL_BC_PIS"]) for rec in m105),
            self._number(m100[0]["VL_BC_CRED"]),
        )
        m500 = self._sped_records(declaration, "M500")
        m505 = self._sped_records(declaration, "M505")
        self.assertEqual(m500[0]["ALIQ_COFINS"], "7,6")
        self.assertEqual(m500[0]["VL_CRED"], "152,00")
        self.assertEqual(
            sorted((rec["NAT_BC_CRED"], rec["CST_COFINS"]) for rec in m505),
            [("01", "50"), ("02", "50")],
        )

    def test_the_credit_of_the_documents_is_the_credit_of_the_assessment(self):
        """Two sources that have to agree: the C170 of the entries and the ledger
        read by the assessment."""
        pis, cofins = self._month_with_credit()
        declaration = self._declaration_july()
        for assessment, register in ((pis, "M100"), (cofins, "M500")):
            credit = sum(
                self._number(rec["VL_CRED"])
                for rec in self._sped_records(declaration, register)
            )
            self.assertAlmostEqual(credit, assessment.credit_total, places=2)
        self.assertAlmostEqual(pis.credit_total, 33.0, places=2)
        self.assertAlmostEqual(cofins.credit_total, 152.0, places=2)

    def test_the_credit_is_discounted_of_the_contribution_of_the_period(self):
        """M100.VL_CRED_DESC up to the contribution due; the rest is the balance;
        M200 sums it and the PVA formula holds: due = contribution - credit."""
        self._month_with_credit()
        declaration = self._declaration_july()
        m100 = self._sped_records(declaration, "M100")[0]
        m200 = self._sped_records(declaration, "M200")[0]
        m210 = self._sped_records(declaration, "M210")
        self.assertEqual(len(m210), 1)
        self.assertEqual(m210[0]["COD_CONT"], "01")
        self.assertEqual(m210[0]["VL_BC_CONT"], "1000,00")
        self.assertEqual(m210[0]["ALIQ_PIS"], "1,65")
        self.assertEqual(m210[0]["VL_CONT_PER"], "16,50")
        self.assertEqual(m100["VL_CRED_DESC"], "16,50")
        self.assertEqual(m100["SLD_CRED"], "16,50")
        # a partial discount, which the PVA tells apart by the indicator
        self.assertEqual(m100["IND_DESC_CRED"], "1")
        self.assertEqual(m200["VL_TOT_CONT_NC_PER"], "16,50")
        self.assertEqual(m200["VL_TOT_CRED_DESC"], m100["VL_CRED_DESC"])
        self.assertEqual(self._number(m200["VL_TOT_CONT_NC_DEV"]), 0.0)
        self.assertEqual(self._number(m200["VL_CONT_NC_REC"]), 0.0)
        m600 = self._sped_records(declaration, "M600")[0]
        m500 = self._sped_records(declaration, "M500")[0]
        self.assertEqual(m600["VL_TOT_CRED_DESC"], m500["VL_CRED_DESC"])
        self.assertEqual(m600["VL_TOT_CRED_DESC"], "76,00")

    def test_the_whole_credit_is_discounted_when_the_contribution_covers_it(self):
        """Contribution above the credit: the indicator says the discount is the
        whole available credit, there is no balance and the rest is due."""
        self._entry("fo_compras_compras_comercializacao", "401")
        self._entry("fo_compras_compras", "402")
        for _index in range(3):
            self._sale()
        self._assess("pis")
        self._assess("cofins")
        declaration = self._declaration_july()
        m100 = self._sped_records(declaration, "M100")[0]
        m200 = self._sped_records(declaration, "M200")[0]
        self.assertEqual(m100["VL_CRED"], "33,00")
        self.assertEqual(m100["IND_DESC_CRED"], "0")
        self.assertEqual(m100["VL_CRED_DESC"], "33,00")
        self.assertEqual(self._number(m100["SLD_CRED"]), 0.0)
        self.assertEqual(m200["VL_TOT_CONT_NC_PER"], "49,50")
        self.assertEqual(m200["VL_TOT_CRED_DESC"], "33,00")
        self.assertEqual(m200["VL_TOT_CONT_NC_DEV"], "16,50")
        self.assertEqual(m200["VL_CONT_NC_REC"], "16,50")

    def test_the_file_stops_when_the_credit_has_no_assessment(self):
        """The M200 comes from the assessment: credit in the documents and no
        posted assessment is a file the PVA would refuse."""
        self._entry("fo_compras_compras_comercializacao", "401")
        self._set_accountant()
        declaration = self._declaration_july()
        with self.assertRaises(UserError) as error:
            declaration.button_create_sped_files()
        self.assertIn("assessment", error.exception.args[0])

    def test_the_file_stops_when_the_assessment_does_not_match_the_documents(self):
        """Posted before a late entry: the credit of the documents is not the
        credit of the assessment, and the message says so."""
        self._entry("fo_compras_compras_comercializacao", "401")
        self._assess("pis")
        self._assess("cofins")
        self._entry("fo_compras_compras", "402")
        self._set_accountant()
        declaration = self._declaration_july()
        with self.assertRaises(UserError) as error:
            declaration.button_create_sped_files()
        self.assertIn(
            "not the credit of the posted assessment", error.exception.args[0]
        )

    def test_the_c170_of_a_non_cumulative_company_carries_the_account(self):
        """The PVA asks the analytic account in the C170 of the sale (CST 01), of
        the entry with credit (CST 50) and of the entry without credit (CST 70)
        of the non-cumulative company, and the 0500 declares each one."""
        self._month_with_credit()
        declaration = self._declaration_july()
        c170 = self._sped_records(declaration, "C170")
        self.assertEqual({rec["CST_PIS"] for rec in c170}, {"01", "50", "70"})
        codes = [rec["COD_CTA"] for rec in self._sped_records(declaration, "0500")]
        for rec in c170:
            self.assertTrue(rec["COD_CTA"], rec["CST_PIS"])
            self.assertIn(rec["COD_CTA"], codes)
        self.assertEqual(len(codes), len(set(codes)))


@tagged("post_install", "-at_install")
class TestSpedPisCofinsCumulativeUnchanged(CreditMixin, SpedEntradaCommon):
    """The Lucro Presumido keeps its file: no credit block, no account of the
    sale (the PVA validates it without)."""

    def test_the_cumulative_company_has_no_credit_block(self):
        self._entry("fo_compras_compras_comercializacao", "401")
        self._sale()
        self._assess("pis", regime="cumulative")
        self._assess("cofins", regime="cumulative")
        declaration = self._declaration_july()
        for register in ("M100", "M105", "M500", "M505"):
            self.assertEqual(self._sped_records(declaration, register), [], register)
        sale_line = [
            rec
            for rec in self._sped_records(declaration, "C170")
            if rec["CST_PIS"] == "01"
        ][0]
        self.assertEqual(sale_line["COD_CTA"], "")
        self.assertEqual(self._sped_records(declaration, "0500"), [])
