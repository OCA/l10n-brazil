from dateutil.relativedelta import relativedelta

from odoo.exceptions import ValidationError
from odoo.fields import Date
from odoo.tests import SavepointCase


class TestHrEmployeeDependent(SavepointCase):
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
                "cnpj_cpf": "853.334.271-35",
            }
        )

        cls.employee_dependent = cls.env["hr.employee.dependent"]
        cls.employee_dependent = cls.employee_dependent.create(
            {
                "employee_id": cls.employee.id,
                "name": "Dependent 01",
                "dependent_dob": "2019-01-01",
                "inscr_est": "49.365.539-6",
                "cnpj_cpf": "417.668.850-55",
                "dependent_type_id": cls.env["hr.dependent.type"].search([])[0].id,
            }
        )

        cls.employee._check_dependents()
        cls.assertTrue(cls.employee, "Error on create a l10n_br employee")
        cls.assertTrue(cls.employee_dependent, "Error on create a employee dependent")

    def test_invalid_hr_employee_dependent_cpf(self):
        try:
            result = self.employee_dependent.write({"cnpj_cpf": "853.334.271-351"})
        except ValidationError:
            result = False

        self.assertFalse(result, "Error on update invalid employee dependent cpf")

    def test_onchange_cpf(self):
        self.employee_dependent.write({"cnpj_cpf": "78004863035"})
        self.employee_dependent.onchange_cpf()

        self.assertEqual(self.employee_dependent.cnpj_cpf, "780.048.630-35")

    def test_check_dob(self):
        """
        Data de nascimento maior do que hoje.
        """
        self.employee_dependent.write(
            {"dependent_dob": Date.today() + relativedelta(days=10)}
        )

        with self.assertRaises(ValidationError) as context:
            self.employee._check_dob()

        self.assertEqual(
            "Invalid birth date for dependent Dependent 01", context.exception.name
        )

    def test_check_dependent_type(self):
        """
        Dependentes do mesmo tipo.
        """
        self.employee_dependent_obj = self.env["hr.employee.dependent"]

        self.employee_dependent_obj.create(
            {
                "employee_id": self.employee.id,
                "name": "Dependent 02",
                "dependent_dob": "2019-01-01",
                "cnpj_cpf": "994.769.750-91",
                "dependent_type_id": self.env.ref("l10n_br_hr.l10n_br_dependent_1").id,
            }
        )

        self.employee_dependent_obj.create(
            {
                "employee_id": self.employee.id,
                "name": "Dependent 03",
                "dependent_dob": "2019-02-01",
                "cnpj_cpf": "362.502.120-00",
                "dependent_type_id": self.env.ref("l10n_br_hr.l10n_br_dependent_1").id,
            }
        )

        with self.assertRaises(ValidationError) as context:
            self.employee._check_dependent_type()

        self.assertEqual(
            "A dependent with the same level of relatedness already "
            "exists for dependent Dependent 02",
            context.exception.name,
        )
