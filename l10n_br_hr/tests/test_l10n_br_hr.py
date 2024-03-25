from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase


class TestL10nBr(TransactionCase):
    def setUp(self):
        super(TestL10nBr, self).setUp()

        self.employee = self.env["hr.employee"]
        self.employee = self.employee.create(
            {
                "address_id": self.env["res.partner"].search([]).company_id.id,
                "company_id": self.env["res.partner"].search([]).company_id.id,
                "department_id": self.env["hr.department"],
                "civil_certificate_type_id": self.env["hr.civil.certificate.type"],
                "deficiency_id": 1,
                "deficiency_description": "Deficiency in index finger",
                "name": "l10n brazil demo employee",
                "pis_pasep": "496.85994.95-6",
                "cpf": "853.334.271-35",
            }
        )

        self.assertTrue(self.employee, "Error on create a l10n_br employee")

    def test_invalid_hr_employee_cpf(self):
        try:
            result = self.employee.write({"cpf": "853.334.271-351"})
        except ValidationError:
            result = False

        self.assertFalse(result, "Error on update invalid employee cpf")

    def test_onchange_cpf(self):
        self.employee.write({"cpf": "78004863035"})
        self.employee.onchange_cpf()
        self.assertEqual(self.employee.cpf, "780.048.630-35")

    def test_invalid_employee_pis_pasep(self):
        try:
            result = self.employee.write({"pis_pasep": "496.851994.95-6"})
        except ValidationError:
            result = False

        self.assertFalse(result, "Error on update invalid employee pis_pasep")

    def test_l10n_br_hr_cbo(self):
        cbo = self.env.ref("l10n_br_hr.1")
        self.assertTrue(
            cbo.name_get()[0][1] == "010105 - Oficial general da " "aeronáutica",
            "The CBO name by name_get is not valid, expected " "'code - name'",
        )

    def test_hr_deficiency(self):
        deficiency_name = self.env["hr.deficiency"].search([])[0].name
        self.assertEqual(
            deficiency_name,
            "Física",
            "The deficiency name get is not valid, expected " "'Física'",
        )

    def test_dependent_type(self):
        dependent_type = self.env["hr.dependent.type"].search([])[0].name_get()[0][1]
        self.assertEqual(
            dependent_type,
            "1 - Cônjuge",
            "The dependent type get is not valid, expected" " '1 - Cônjuge'",
        )

    def test_hr_ethnicity(self):
        ethnicity = self.env["hr.ethnicity"].search([])[0].name_get()[0][1]
        self.assertEqual(
            ethnicity,
            "1 - Branca",
            "The ethnicity get is not valid, expectded" " '1 - Branca'",
        )

    def test_hr_educational_attainment(self):
        educational_attainment = self.env["hr.educational.attainment"]
        educational_attainment = educational_attainment.search([])[0].name_get()[0][1]
        expected_result = (
            "01 - Analfabeto, inclusive o que, embora tenha "
            "recebido instrução, não se alfabetizou"
        )
        self.assertEqual(
            educational_attainment,
            expected_result,
            "The educational attainment get is not valid,"
            " expected '" + expected_result + "'",
        )
