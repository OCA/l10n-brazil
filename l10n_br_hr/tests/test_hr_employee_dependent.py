from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase


class TestHrEmployeeDependent(TransactionCase):

    def setUp(self):
        super(TestHrEmployeeDependent, self).setUp()

        self.employee = self.env['hr.employee']
        self.employee = self.employee.create({
            'address_id': self.env['res.partner'].search([])[0].company_id.id,
            'company_id': self.env['res.partner'].search([])[0].company_id.id,
            'department_id': self.env['hr.department'],
            'civil_certificate_type_id': self.env['hr.civil.certificate.type'],
            'deficiency_id': 1,
            'deficiency_description': 'Deficiency in index finger',
            'name': 'l10n brazil demo employee',
            'pis_pasep': '496.85994.95-6',
            'cpf': '853.334.271-35',
        })

        self.employee_dependent = self.env['hr.employee.dependent']
        self.employee_dependent = self.employee_dependent.create({
            'employee_id':  self.employee.id,
            'dependent_name': 'Dependent 01',
            'dependent_dob': '2019-01-01',
            'dependent_type_id': self.env['hr.dependent.type'].search([])[0].id,
            'dependent_rg': '49.365.539-6',
            'dependent_cpf': '417.668.850-55',
            'partner_id': self.env['res.partner'].search([])[0].company_id.id,
        })


        self.assertTrue(self.employee, 'Error on create a l10n_br employee')
        self.assertTrue(
            self.employee_dependent, 'Error on create a employee dependent')

    def test_invalid_hr_employee_dependent_cpf(self):
        try:
            result = self.employee_dependent.write({
                'dependent_cpf': '853.334.271-351',
            })
        except ValidationError:
            result = False

        self.assertFalse(
            result, 'Error on update invalid employee dependent cpf')

    def test_onchange_cpf(self):
        self.employee_dependent.write({'dependent_cpf': '78004863035'})
        self.employee_dependent.onchange_cpf()

        self.assertEqual(
            self.employee_dependent.dependent_cpf, '780.048.630-35')
