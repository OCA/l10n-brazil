from odoo.tests import TransactionCase


class TestL10nBr(TransactionCase):

    def test_hr_employee(self):
        result = False

        employee = self.env['hr.employee']
        result = employee.create({
            'address_id': self.env['res.partner'].search([])[0].company_id.id,
            'company_id': self.env['res.partner'].search([])[0].company_id.id,
            'department_id': self.env['hr.department'],
            'civil_certificate_type_id': self.env['hr.civil.certificate.type'],
            'deficiency_id': 1,
            'deficiency_description': 'Deficiency in index finger',
            'chronic_disease_ids': 'Cronic',
            'name': 'l10n brazil demo employee',
            'pis_pasep': '496.85994.95-6',
            'cpf': '853.334.271-35',
        })

        self.assertTrue(result, 'Error on create a l10n_br employee')

    def test_L10nBrHrCbo(self):
        cbo = self.env.ref('l10n_br_hr.1')
        self.assertTrue(cbo.name_get()[0][1] == '010105 - Oficial general da aeronáutica',
                        'The CBO name by name_get is not valid, expected \'code - name\'')

    def test_HrDeficiency(self):
        deficiency_name = self.env['hr.deficiency'].search([])[0].name
        self.assertEqual(deficiency_name, 'Física',
                         'The deficiency name get is not valid, expected \'Física\'')

    def test_DependentType(self):
        dependent_type = self.env['hr.dependent.type'].search([])[0].name
        self.assertEqual(dependent_type, 'Cônjuge',
                         'The dependent type get is not valid, expected \'Cônjuge\'')

    def test_HrEthnicity(self):
        ethnicity = self.env['hr.ethnicity'].search([])[0].name
        self.assertEqual(ethnicity, 'Branca',
                         'The ethnicity get is not valid, expectded \'Branca\'')

    def test_HrEducationalAttainment(self):
        educational_attainment = self.env['hr.educational.attainment'].search([])[
            0].name
        expected_result = 'Analfabeto, inclusive o que, embora tenha recebido instrução, não se alfabetizou'
        self.assertEqual(educational_attainment, expected_result,
                         'The educational attainment get is not valid, expected \'' + expected_result + '\'')

    def test_HrNationalityCode(self):
        nationality_code = self.env['hr.nationality.code'].search([])[0].code
        self.assertEqual(nationality_code, '10',
                         'The nationality code is not valid, expected \'10\'')
