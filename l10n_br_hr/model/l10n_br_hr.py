# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models


class L10nBrHrCbo(models.Model):
    _name = "l10n_br_hr.cbo"
    _description = "Brazilian Classification of Occupation"

    code = fields.Char('Code', required=True)
    name = fields.Char('Name', size=255, required=True, translate=True)

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record['name']
            if record['code']:
                name = record['code'] + ' - ' + name
            result.append((record['id'], name))
        return result


class HrDeficiency(models.Model):
    _name = 'hr.deficiency'

    name = fields.Char(string='Deficiency')
    code = fields.Char(string='Code')

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record['name']
            if record['code']:
                name = record['code'] + ' - ' + name
            result.append((record['id'], name))
        return result


class HrIdentityType(models.Model):
    _name = 'hr.identity.type'

    name = fields.Char(string='Identity type')
    initials = fields.Char(string='Initials')
    employee_ids = fields.Many2many(string=u"Employees",
                                    comodel_name='hr.employee')


class HrCivilCertificateType(models.Model):
    _name = 'hr.civil.certificate.type'

    name = fields.Char(string='Civil certificate type')


class HrChronicDisease(models.Model):
    _name = 'hr.chronic.disease'

    name = fields.Char(string='Disease name')
    employee_ids = fields.Many2many(string="Employee",
                                    comodel_name='hr.employee')


class HrDependentType(models.Model):
    _name = 'hr.dependent.type'

    name = fields.Char(string='Relatedness degree')
    code = fields.Char(string='Code')

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record['name']
            if record['code']:
                name = record['code'] + ' - ' + name
            result.append((record['id'], name))
        return result


class HrEthnicity(models.Model):
    _name = 'hr.ethnicity'

    name = fields.Char(string='Ethnicity')
    code = fields.Char('code')

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record['name']
            if record['code']:
                name = record['code'] + ' - ' + name
            result.append((record['id'], name))
        return result


class HrEducationalAttainment(models.Model):
    _name = 'hr.educational.attainment'

    name = fields.Char(string='Educational Attainment')
    code = fields.Char(string='Code')

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record['name']
            if record['code']:
                name = record['code'] + ' - ' + name
            result.append((record['id'], name))
        return result


class HrNationalityCode(models.Model):
    _name = 'hr.nationality.code'

    name = fields.Char(string='Nationality')
    code = fields.Char(string='Code')

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record['name']
            if record['code']:
                name = record['code'] + ' - ' + name
            result.append((record['id'], name))
        return result
