# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Rafael da Silva Lima <rafael.lima@kmee.com.br>
# (c) 2014 Kmee - Matheus Felix <matheus.felix@kmee.com.br>
# (c) 2016 KMEE Informática - Daniel Sadamo <daniel.sadamo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.addons.l10n_br_base.tools import fiscal
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    naturalidade = fields.Many2one(
        string='Naturalidade',
        comodel_name='l10n_br_base.city',
    )

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
        for record in self:
            if record.pis_pasep and not fiscal.\
                    validate_pis_pasep(record.pis_pasep):
                raise ValidationError(_('Invalid PIS/PASEP'))

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
                                   default='3')
    educational_attainment = fields.Many2one(
        string='Educational attainment',
        comodel_name='hr.educational.attainment',
        track_visibility='onchange',
    )
    have_dependent = fields.Boolean('Has dependents',
                                    track_visibility='onchange')
    dependent_ids = fields.One2many(comodel_name='hr.employee.dependent',
                                    inverse_name='employee_id',
                                    string='Dependents')
    rg = fields.Char(
        string='RG',
        store=True,
        related='address_home_id.inscr_est',
        help='National ID number'
    )
    cpf = fields.Char(
        string='CPF',
        store=True,
        related='address_home_id.cnpj_cpf'
    )

    @api.onchange('cpf')
    def onchange_cpf(self):
        country = self.env['res.country'].\
            search([('id', '=', self.country_id.id)]).code or ''
        cpf = fiscal.format_cpf_cnpj(self.cpf, country, False)
        if cpf:
            self.cpf = cpf

    @api.multi
    @api.constrains('cpf')
    def _check_cpf(self):
        for record in self:
            if record.cpf and not fiscal.validate_cpf(record.cpf):
                raise ValidationError(u"CPF Invalido!")

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
    ethnicity = fields.Many2one(string='Ethnicity',
                                comodel_name='hr.ethnicity')
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
    deficiency_id = fields.Many2one(string='Deficiency',
                                    comodel_name='hr.deficiency',
                                    track_visibility='onchange')
    deficiency_description = fields.Char(string='Deficiency description')
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
        ('common_law_marriage', 'Common law marriage'),
        ('separated', 'Separated')])
    registration = fields.Char(string='Registration number')
    nationality_code = fields.Many2one(string='Nationality code',
                                       comodel_name='hr.nationality.code')
    nat_code = fields.Char(related='nationality_code.code')
    arrival_year = fields.Integer(string="Arrival year in Brazil")
    country_id = fields.Many2one(comodel_name='res.country',
                                 default=_default_country)


class HrEmployeeDependent(models.Model):
    _name = 'hr.employee.dependent'
    _description = 'Employee\'s Dependents'
    _rec_name = "dependent_name"

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

    have_alimony = fields.Boolean(string='Tem Pensão?')

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        help="Parceiro que contem as informações de banco do dependente."
    )

    partner_id_bank_ids = fields.One2many(
        comodel_name='res.partner.bank',
        string='Info Bank',
        related='partner_id.bank_ids',
    )
