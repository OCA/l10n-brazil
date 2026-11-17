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
                "cpf": "853.334.271-35",
            }
        )

        cls.assertTrue(cls.employee, "Error on create a l10n_br employee")

    def test_invalid_hr_employee_cpf(self):
        try:
            result = self.employee.write({"cpf": "853.334.271-351"})
        except ValidationError:
            result = False

        self.assertFalse(result, "Error on update invalid employee cpf")

    def test_onchange_cpf(self):
        self.employee.write({"cpf": "780.048.630-35"})
        self.employee.onchange_cpf()
        self.assertEqual(self.employee.cpf, "78004863035")

    def test_cpf_stored_unformatted(self):
        """The CPF is stored as plain digits on the work contact vat,
        following the l10n_br_base convention (eSocial ready)."""
        self.employee.write({"cpf": "780.048.630-35"})
        self.assertEqual(self.employee.cpf, "78004863035")
        self.assertEqual(self.employee.work_contact_id.vat, "78004863035")

    def test_cpf_propagated_on_create(self):
        """A cpf given at creation time lands on the auto-created work
        contact vat (the hr module creates the work contact only after
        the related field inverse ran)."""
        employee = self.env["hr.employee"].create(
            {"name": "create-time cpf", "cpf": "780.048.630-35"}
        )
        self.assertEqual(employee.cpf, "78004863035")
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

    def test_onchange_cpf_empty(self):
        self.employee.cpf = ""
        self.employee.onchange_cpf()
        self.assertFalse(self.employee.cpf)

    def test_invalid_employee_pis_pasep(self):
        try:
            result = self.employee.write({"pis_pasep": "496.851994.95-6"})
        except ValidationError:
            result = False

        self.assertFalse(result, "Error on update invalid employee pis_pasep")

    def test_l10n_br_hr_cbo(self):
        cbo = self.env.ref("l10n_br_hr.1")
        self.assertTrue(
            cbo.display_name == "010105 - Oficial general da aeronáutica",
            "The CBO name is not valid, expected 'code - name'",
        )

    def test_hr_deficiency(self):
        deficiency_name = self.env["hr.deficiency"].search([])[0].name
        self.assertEqual(
            deficiency_name,
            "Física",
            "The deficiency name get is not valid, expected 'Física'",
        )

    def test_hr_ethnicity(self):
        ethnicity = self.env["hr.ethnicity"].search([])[0].display_name
        self.assertEqual(
            ethnicity,
            "1 - Branca",
            "The ethnicity display_name is not valid, expected '1 - Branca'",
        )

    def test_marital_status_selection(self):
        selection = self.env["hr.version"]._get_marital_status_selection()
        selection_keys = [item[0] for item in selection]
        self.assertIn("common_law_marriage", selection_keys)
        self.assertIn("separated", selection_keys)
        self.employee.marital = "common_law_marriage"
        self.assertEqual(self.employee.marital, "common_law_marriage")
        self.employee.marital = "separated"
        self.assertEqual(self.employee.marital, "separated")
