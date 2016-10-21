# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Rafael da Silva Lima <rafael.lima@kmee.com.br>
# (c) 2014 Kmee - Matheus Felix <matheus.felix@kmee.com.br>
# (c) 2016 KMEE Informática - Daniel Sadamo <daniel.sadamo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api, _
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.addons.l10n_br_base.tools import fiscal
from openerp.exceptions import ValidationError


NATIONALITY_CODE = [
    ('10', '10 - BRAZILIAN'),
    ('20', '20 - BRAZILIAN NATURALIZED'),
    ('21', '21 - ARGENTINE'),
    ('22', '22 - BOLIVIAN'),
    ('23', '23 - CHILEAN'),
    ('24', '24 - PARAGUAYAN'),
    ('25', '25 - URUGUAYAN'),
    ('26', '26 - VENEZUELAN'),
    ('27', '27 - COLOMBIAN'),
    ('28', '28 - PERUVIAN'),
    ('29', '29 - ECUADORIAN'),
    ('30', '30 - GERMAN'),
    ('31', '31 - BELGIAN'),
    ('32', '32 - BRITISH'),
    ('34', '34 - CANADIAN'),
    ('35', '35 - SPANISH'),
    ('36', '36 - NORTH-AMERICAN'),
    ('37', '37 - FRENCH'),
    ('38', '38 - SWISS'),
    ('39', '39 - ITALIAN'),
    ('40', '40 - HAITIAN'),
    ('41', '41 - JAPANESE'),
    ('42', '42 - CHINESE'),
    ('43', '43 - KOREAN'),
    ('44', '44 - RUSSIAN'),
    ('45', '45 - PORTUGUESE'),
    ('46', '46 - PAKISTANI'),
    ('47', '47 - INDIAN'),
    ('48', '48 - OTHER LATIN-AMERICAN'),
    ('49', '49 - OTHER ASIAN'),
    ('50', '50 - BANGLA'),
    ('51', '51 - OTHER EUROPEAN'),
    ('60', '60 - ANGOLAN'),
    ('61', '61 - CONGOLESE'),
    ('62', '62 - SOUTH AFRICAN'),
    ('63', '63 - GHANAIAN'),
    ('64', '64 - SENEGALESE'),
    ('70', '70 - OTHER AFRICAN'),
    ('80', '80 - OTHER')
]


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def _default_country(self):
        return self.env['res.country'].search([('code', '=', 'BR')])

    @api.constrains('dependent_ids')
    def _check_dependents(self):
        self._check_dob()
        self._check_dependent_type()

    def _check_dob(self):
        for dependent in self.dependent_ids:
            if datetime.strptime(
                    dependent.dependent_dob, DEFAULT_SERVER_DATE_FORMAT
                    ).date() > datetime.now().date():
                raise ValidationError(_('Invalid birth date for dependent %s'
                                        % dependent.dependent_name))

    def _check_dependent_type(self):
        seen = set()
        restrictions = (
            self.env.ref('l10n_br_hr.l10n_br_dependent_1'),
            self.env.ref('l10n_br_hr.l10n_br_dependent_9_1'),
            self.env.ref('l10n_br_hr.l10n_br_dependent_9_2')
        )
        for dependent in self.dependent_ids:
            dep_type = dependent.dependent_type_id
            if dep_type not in seen and dep_type in restrictions:
                seen.add(dep_type)
            elif dep_type in seen and dep_type in restrictions:
                raise ValidationError(
                    _('A dependent with the same level of relatedness'
                      ' already exists for dependent %s'
                      % dependent.dependent_name))

    @api.constrains('pis_pasep')
    def _validate_pis_pasep(self):
        employee = self
        if not employee.pis_pasep:
            return True
        elif fiscal.validate_pis_pasep(self.pis_pasep):
            return True
        else:
            raise ValidationError(_('Invalid PIS/PASEP'))

    check_cpf = fields.Boolean('Check CPF', default=True)
    pis_pasep = fields.Char(u'PIS/PASEP', size=15)
    ctps = fields.Char('CTPS', help='CTPS number')
    ctps_series = fields.Char('CTPS series')
    ctps_date = fields.Date('CTPS emission date')
    ctps_uf_id = fields.Many2one(string='CTPS district',
                                 comodel_name='res.country.state')
    creservist = fields.Char('Military service status certificate')
    cresv_categ = fields.Selection(string='Military service status category',
                                   selection=[
                                       ('1', 'First Category'),
                                       ('2', 'Second Category'),
                                       ('3', 'Third Category')],
                                   default=('3', 'Third Category'))
    ginstru = fields.Selection(
        string='Educational attainment',
        selection=[
            ('incomplete_elementary_school', 'Incomplete elementary school'),
            ('complete_elementary_school', 'Complete elementary school'),
            ('incomplete_high_school', 'Incomplete high school'),
            ('complete_high_school', 'Complete high school'),
            ('incomplete_graduation', 'Incomplete graduation'),
            ('Graduation', 'Complete graduation'),
            ('master', 'Master'),
            ('phd', 'Ph.D')
        ])
    have_dependent = fields.Boolean('Has dependents')
    dependent_ids = fields.One2many(comodel_name='hr.employee.dependent',
                                    inverse_name='employee_id',
                                    string='Dependents')
    rg = fields.Char(string='RG', help='National ID number')
    cpf = fields.Char(string='CPF', related='address_home_id.cnpj_cpf',
                      required=True)
    organ_exp = fields.Char(string='Dispatcher organ')
    rg_emission = fields.Date(string='Emission date')
    voter_title = fields.Char(string='Voter title')
    voter_zone = fields.Char(string='Voter zone')
    voter_section = fields.Char(string='Voter section')
    driver_license = fields.Char(string='Driver license number')
    driver_categ = fields.Char(string='Driver license category')
    father_name = fields.Char(string='Father name')
    mother_name = fields.Char(string='Mother name')
    expiration_date = fields.Date(string='Expiration date')
    ethnicity = fields.Selection(string='Ethnicity', selection=[
        ('indigene', 'Indigene'),
        ('white', 'White'),
        ('black', 'Black'),
        ('asian', 'Asian'),
        ('pardo', 'Pardo'),
        ('not_informed', 'Not informed')
    ])
    blood_type = fields.Selection(string='Blood type', selection=[
        ('a+', 'A+'),
        ('a-', 'A-'),
        ('b+', 'B+'),
        ('b-', 'B-'),
        ('o+', 'O+'),
        ('o-', 'O-'),
        ('ab+', 'AB+'),
        ('ab-', 'AB-'),
    ])
    deficiencies_ids = fields.Many2many(string='Deficiencies',
                                        comodel_name='hr.deficiency')
    identity_type_id = fields.Many2one(string='ID type',
                                       comodel_name='hr.identity.type')
    identity_validity = fields.Date(string='ID expiration date')
    identity_uf_id = fields.Many2one(string='ID expedition district',
                                     comodel_name='res.country.state')
    identity_city_id = fields.Many2one(
        string='ID expedition city',
        comodel_name='l10n_br_base.city',
        domain="[('state_id','=',identity_uf_id)]")
    civil_certificate_type_id = fields.Many2one(
        string='Civil certificate type',
        comodel_name='hr.civil.certificate.type')
    alternate_phone = fields.Char(string='Alternate phone')
    emergency_phone = fields.Char(string='Emergency phone')
    talk_to = fields.Char(string='Emergency contact name')
    alternate_email = fields.Char(string='Alternate email')
    chronic_disease_ids = fields.Many2many(string='Chronic Diseases',
                                           comodel_name='hr.chronic.disease')
    marital = fields.Selection(selection_add=[
        ('common_law_marriage', 'Common law marriage'), ('separated', 'Separated')])
    registration = fields.Char(string='Registration number')
    nationality_code = fields.Selection(string='Nationality code',
                                        selection=NATIONALITY_CODE)
    arrival_year = fields.Integer(string="Arrival year in Brazil")
    country_id = fields.Many2one(comodel_name='res.country',
                                 default=_default_country)

    @api.model
    @api.onchange('address_home_id')
    def onchange_address_home_id(self):
        if self.address_home_id:
            if self.address_home_id.cnpj_cpf:
                self.check_cpf = True
                self.cpf = self.address_home_id.cnpj_cpf
            else:
                self.check_cpf = False
                self.cpf = False

    @api.multi
    def onchange_user(self, user_id):
        res = super(HrEmployee, self).onchange_user(user_id)
        partner = self.env['res.partner'].search(
            [('user_ids', '=', user_id)], limit=1)
        res['value'].update({'address_home_id': partner.id})
        return res


class HrEmployeeDependent(models.Model):
    _name = 'hr.employee.dependent'
    _description = 'Employee\'s Dependents'

    @api.constrains('dependent_cpf')
    def _validate_cpf(self):
        if self.dependent_cpf:
            if not fiscal.validate_cpf(self.dependent_cpf):
                raise ValidationError(_('Invalid CPF for dependent %s'
                                        % self.dependent_name))

    employee_id = fields.Many2one(comodel_name='hr.employee',
                                  string='Employee')
    dependent_name = fields.Char(string='Name', size=64, required=True)
    dependent_dob = fields.Date(string='Date of birth', required=True)
    dependent_type_id = fields.Many2one(string='Relatedness',
                                        required=True,
                                        comodel_name='hr.dependent.type')
    pension_benefits = fields.Float(string='Allowance value')
    dependent_verification = fields.Boolean(string='Is dependent')
    health_verification = fields.Boolean(string='Healthcare plan')
    dependent_gender = fields.Selection(string='Gender', selection=[
        ('m', 'Male'),
        ('f', 'Female')])
    dependent_rg = fields.Char(string='RG')
    dependent_cpf = fields.Char(string='CPF')
