# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

import base64
from datetime import date

from odoo.exceptions import UserError
from odoo.tests.common import tagged

from odoo.addons.l10n_br_tax_assessment.tests.common_entrada import SpedEntradaCommon

from .test_sped_entrada import EntradaHelpers


@tagged("post_install", "-at_install")
class TestSpedEfdIcmsIpiApuracao(EntradaHelpers, SpedEntradaCommon):
    """The entry in the books and in the ICMS assessment (E110)."""

    def _set_accountant(self):
        city = self.env["res.city"].search([("state_id.code", "=", "SP")], limit=1)
        self.company.accountant_id = self.env["res.partner"].create(
            {
                "name": "Accountant",
                "is_accountant": True,
                "cnpj_cpf": "111.444.777-35",
                "crc_code": "1SP123456/O-0",
                "phone": "11999999999",
                "email": "accountant@example.com",
                "country_id": self.env.ref("base.br").id,
                "state_id": self.env.ref("base.state_br_sp").id,
                "city_id": city.id,
            }
        )

    def test_generation_stops_without_the_posted_icms_assessment(self):
        """No assessment, no E110, and the PVA refuses the file: the generation
        stops with a message that says what to do."""
        self._set_accountant()
        self._purchase_move("fo_compras_compras_comercializacao", "601")
        declaration = self._declaration_july()
        with self.assertRaises(UserError) as error:
            declaration.button_create_sped_files()
        self.assertIn("ICMS", error.exception.args[0])

    def test_e110_credits_match_the_c190_of_the_entries(self):
        """The PVA crosses E110 field 5 with the ICMS of the entry C190: both
        come from what the company has the right to credit."""
        self._purchase_move("fo_compras_compras_comercializacao", "604")
        self._assess_icms_of_july()
        declaration = self._declaration_july()
        c190_credit = sum(
            self._number(rec["VL_ICMS"])
            for rec in self._sped_records(declaration, "C190")
            if rec["CFOP"].startswith(("1", "2", "3"))
        )
        e110 = self._sped_records(declaration, "E110")
        self.assertEqual(len(e110), 1)
        self.assertEqual(self._number(e110[0]["VL_TOT_CREDITOS"]), c190_credit)
        self.assertGreater(c190_credit, 0)
        # and the file is generated (a company that is not an IPI taxpayer)
        self._set_accountant()
        declaration.IND_ATIV = "1"
        declaration.button_create_sped_files()
        self.assertTrue(declaration.message_ids)

    def test_generation_stops_without_an_accountant(self):
        self._purchase_move("fo_compras_compras_comercializacao", "606")
        declaration = self._declaration_july()
        self.company.accountant_id = False
        with self.assertRaises(UserError) as error:
            declaration.button_create_sped_files()
        self.assertIn("accountant", error.exception.args[0])

    def test_the_activity_and_the_classification_follow_the_company(self):
        """An IPI taxpayer is industrial with its classification; any other
        company is Outros, and the industrial one needs the IPI assessment."""
        self.assertEqual(self.company.industry_type, "00")
        declaration = self.env["l10n_br_sped.efd_icms_ipi.0000"].create(
            {
                "company_id": self.company.id,
                "DT_INI": "2026-07-01",
                "DT_FIN": "2026-07-31",
            }
        )
        self.assertEqual(declaration.IND_ATIV, "0")
        self.assertEqual(declaration.CLAS_ESTAB_IND, "00")
        self.company.write({"is_industry": False, "ripi": False})
        declaration._onchange_company_activity()
        self.assertEqual(declaration.IND_ATIV, "1")
        self.assertFalse(declaration.CLAS_ESTAB_IND)

    def test_an_industrial_declaration_needs_the_ipi_assessment(self):
        self._set_accountant()
        self._purchase_move("fo_compras_compras_comercializacao", "607")
        self._assess_icms_of_july()
        declaration = self._declaration_july()
        self.assertEqual(declaration.IND_ATIV, "0")
        with self.assertRaises(UserError) as error:
            declaration.button_create_sped_files()
        self.assertIn("IPI", error.exception.args[0])

    def _generated_text(self, declaration):
        attachment = self.env["ir.attachment"].search(
            [("res_model", "=", declaration._name), ("res_id", "=", declaration.id)],
            order="id desc",
            limit=1,
        )
        return base64.b64decode(attachment.datas).decode("latin-1")

    def test_the_file_has_the_registers_of_the_moment_of_the_generation(self):
        """The registers pulled before the assessment and the accountant are
        pulled again when the file is generated: no E110 or 0100 missing from a
        file made after the registration was fixed."""
        self._purchase_move("fo_compras_compras_comercializacao", "607")
        declaration = self._declaration_july()
        self.assertEqual(self._sped_records(declaration, "E110"), [])
        self._set_accountant()
        self._assess_icms_of_july()
        declaration.IND_ATIV = "1"
        declaration.button_create_sped_files()
        text = self._generated_text(declaration)
        self.assertIn("|E110|", text)
        self.assertIn("|0100|", text)

    def test_the_0100_stays_when_the_accountant_has_no_phone(self):
        """The phone is optional in the layout. The mapping broke on a missing
        one and the 0100 went out of the file with no word."""
        self._set_accountant()
        self.company.accountant_id.phone = False
        declaration = self._declaration_july()
        records = self._sped_records(declaration, "0100")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["FONE"], "")

    def test_generation_stops_with_what_the_accountant_lacks(self):
        """The mandatory fields of the 0100 (descriptor of the PVA) that the
        registration of the accountant does not have, said by name."""
        self._set_accountant()
        self.company.accountant_id.write({"email": False, "city_id": False})
        self._purchase_move("fo_compras_compras_comercializacao", "608")
        declaration = self._declaration_july()
        with self.assertRaises(UserError) as error:
            declaration.button_create_sped_files()
        self.assertIn("e-mail", error.exception.args[0])
        self.assertIn("city", error.exception.args[0])

    def test_generation_stops_when_an_earlier_month_was_never_assessed(self):
        """The same hole of the credit balance in the ICMS: June has movement and no
        assessment, so the balance that July starts from is not the real one."""
        self.company.tax_assessment_start = date(2026, 6, 1)
        self._purchase_move(
            "fo_compras_compras_comercializacao", "609", invoice_date=date(2026, 6, 10)
        )
        self._purchase_move("fo_compras_compras_comercializacao", "610")
        self._assess_icms_of_july()
        self._set_accountant()
        declaration = self._declaration_july()
        declaration.IND_ATIV = "1"
        with self.assertRaises(UserError) as error:
            declaration.button_create_sped_files()
        self.assertIn("06/2026", error.exception.args[0])

    def _old_base(self):
        """A base that has years of movement and never used the assessment of the
        system: bills of 2024 and 2025 and of the months of 2026."""
        for number, when in (
            ("701", date(2024, 6, 10)),
            ("702", date(2025, 6, 10)),
            ("703", date(2026, 7, 10)),
            ("704", date(2026, 8, 10)),
        ):
            self._purchase_move(
                "fo_compras_compras_comercializacao", number, invoice_date=when
            )

    def test_an_existing_base_with_years_of_movement_starts_where_it_is_told(self):
        """With the start of the assessment defined in July, July is assessed and
        its file generated: the years before are not asked for one by one."""
        self._old_base()
        self.company.tax_assessment_start = date(2026, 7, 1)
        self._set_accountant()
        self._assess_icms_of_july()
        declaration = self._declaration_july()
        declaration.IND_ATIV = "1"
        declaration.button_create_sped_files()
        self.assertIn("|E110|", self._generated_text(declaration))

    def test_the_month_after_the_start_needs_the_month_before_posted(self):
        """August assessed and posted with July never posted: the file of August
        stops and says July, and says nothing of 2024 and 2025."""
        self._old_base()
        self.company.tax_assessment_start = date(2026, 7, 1)
        self._set_accountant()
        self._assess_icms_of_july(month=8)
        declaration = self._declaration(
            "efd_icms_ipi", date(2026, 8, 1), date(2026, 8, 31)
        )
        declaration.IND_ATIV = "1"
        with self.assertRaises(UserError) as error:
            declaration.button_create_sped_files()
        message = error.exception.args[0]
        self.assertIn("07/2026", message)
        self.assertNotIn("2024", message)
        self.assertNotIn("2025", message)

    def test_without_the_start_the_assessment_asks_for_it(self):
        """An existing base without the date does not get the whole history asked
        for: the assessment asks for the start, with the menu path."""
        self._old_base()
        with self.assertRaises(UserError) as error:
            self._assess_icms_of_july()
        message = error.exception.args[0]
        self.assertIn("Defina o início da apuração pelo sistema", message)
        self.assertIn("aba Fiscal", message)
