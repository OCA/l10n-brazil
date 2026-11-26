import importlib.util

from odoo.exceptions import ValidationError
from odoo.modules.module import get_resource_path
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

    def test_hr_ethnicity(self):
        ethnicity = self.env["hr.ethnicity"].search([])[0].name_get()[0][1]
        self.assertEqual(
            ethnicity,
            "1 - Branca",
            "The ethnicity get is not valid, expectded" " '1 - Branca'",
        )

    def test_l10n_br_hr_cbo_obsolete(self):
        obsolete = self.env.ref("l10n_br_hr.912")  # 322105
        successor = self.env.ref("l10n_br_hr.2637")  # 322705
        self.assertFalse(obsolete.active)
        self.assertTrue(successor.active)
        job = self.env["hr.job"].create(
            {"name": "Acupuncturist", "cbo_id": obsolete.id}
        )
        path = get_resource_path(
            "l10n_br_hr", "migrations", "16.0.4.6.0", "post-migration.py"
        )
        spec = importlib.util.spec_from_file_location("cbo_post_migration", path)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        migration.migrate(self.env.cr, "16.0.4.5.0")
        self.env.invalidate_all()
        self.assertEqual(job.cbo_id, successor)
