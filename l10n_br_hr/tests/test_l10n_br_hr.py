from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase


class TestL10nBr(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.employee = cls.env["hr.employee"]
        cls.employee = cls.employee.create(
            {
                "address_id": cls.env["res.partner"].search([]).company_id.id,
                "company_id": cls.env["res.partner"].search([]).company_id.id,
                "department_id": cls.env["hr.department"],
                "civil_certificate_type_id": cls.env["hr.civil.certificate.type"],
                "deficiency_id": 1,
                "deficiency_description": "Deficiency in index finger",
                "name": "l10n brazil demo employee",
                "pis_pasep": "496.85994.95-6",
                "vat": "853.334.271-35",
            }
        )

        cls.assertTrue(cls.employee, "Error on create a l10n_br employee")

    def test_invalid_hr_employee_cpf(self):
        try:
            result = self.employee.write({"vat": "853.334.271-351"})
        except ValidationError:
            result = False

        self.assertFalse(result, "Error on update invalid employee cpf")

    def test_cpf_formatted(self):
        """The masked CPF is exposed by vat_formatted_cnpj while vat keeps
        the plain digits (l10n_br_base convention, eSocial ready)."""
        self.employee.write({"vat_formatted_cnpj": "780.048.630-35"})
        self.assertEqual(self.employee.vat, "78004863035")
        self.assertEqual(self.employee.vat_formatted_cnpj, "780.048.630-35")
        self.assertEqual(self.employee.work_contact_id.vat, "78004863035")

    def test_cpf_stored_unformatted(self):
        """The employee vat (CPF) is stored as plain digits and lands on
        the work contact vat, following the l10n_br_base convention
        (eSocial ready)."""
        self.employee.write({"vat": "780.048.630-35"})
        self.assertEqual(self.employee.vat, "78004863035")
        self.assertEqual(self.employee.work_contact_id.vat, "78004863035")

    def test_cpf_propagated_on_create(self):
        """A vat (CPF) given at creation time lands on the auto-created work
        contact vat (the hr module creates the work contact only after
        the related field inverse ran)."""
        employee = self.env["hr.employee"].create(
            {"name": "create-time cpf", "vat": "780.048.630-35"}
        )
        self.assertEqual(employee.vat, "78004863035")
        self.assertEqual(employee.work_contact_id.vat, "78004863035")

    def test_pis_pasep_sanitized(self):
        """PIS/PASEP is stored as plain digits (eSocial ready) while the
        formatted value is exposed by pis_pasep_formatted."""
        self.employee.write({"pis_pasep": "496.85994.95-6"})
        self.assertEqual(self.employee.pis_pasep, "49685994956")
        self.assertEqual(self.employee.pis_pasep_formatted, "496.85994.95-6")

    def test_pis_pasep_formatted_inverse(self):
        self.employee.write({"pis_pasep_formatted": "496.85994.95-6"})
        self.assertEqual(self.employee.pis_pasep, "49685994956")

    def test_invalid_employee_pis_pasep(self):
        try:
            result = self.employee.write({"pis_pasep": "496.851994.95-6"})
        except ValidationError:
            result = False

        self.assertFalse(result, "Error on update invalid employee pis_pasep")

    def test_l10n_br_hr_cbo(self):
        cbo = self.env.ref("l10n_br_hr.1")
        self.assertTrue(
            cbo.display_name == "010105 - Oficial general da " "aeronáutica",
            "The CBO name by display_name is not valid, expected " "'code - name'",
        )

    def test_hr_deficiency(self):
        deficiency_name = self.env["hr.deficiency"].search([])[0].name
        self.assertEqual(
            deficiency_name,
            "Física",
            "The deficiency name get is not valid, expected " "'Física'",
        )

    def test_hr_ethnicity(self):
        ethnicity = self.env["hr.ethnicity"].search([])[0].display_name
        self.assertEqual(
            ethnicity,
            "1 - Branca",
            "The ethnicity get is not valid, expectded" " '1 - Branca'",
        )
