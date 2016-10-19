# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields


class L10nBrHrCbo(models.Model):
    _name = "l10n_br_hr.cbo"
    _description = "Brazilian Classification of Occupation"

    code = fields.Integer('Code', required=True)
    name = fields.Char('Name', size=255, required=True, translate=True)


class HrDeficiency(models.Model):
    _name = 'hr.deficiency'

    name = fields.Char(string=u'Deficiência')
    employee_ids = fields.Many2many(string=u"Funcionários",
                                    comodel_name='hr.employee')


class HrIdentityType(models.Model):
    _name = 'hr.identity.type'

    name = fields.Char(string='Tipo de identidade')
    initials = fields.Char(string='Sigla')
    employee_ids = fields.Many2many(string=u"Funcionários",
                                    comodel_name='hr.employee')


class HrCivilCertificateType(models.Model):
    _name = 'hr.civil.certificate.type'

    name = fields.Char(string=u'Tipo de certidão civil')


class HrChronicDisease(models.Model):
    _name = 'hr.chronic.disease'

    name = fields.Char(string=u'Nome da doença')
    employee_ids = fields.Many2many(string=u"Funcionários",
                                    comodel_name='hr.employee')


class HrAdmissionType(models.Model):
    _name = 'hr.admission.type'

    name = fields.Char(string=u'Tipo de admissão')


class HrEmploymentRelationship(models.Model):
    _name = 'hr.employment.relationship'

    name = fields.Char(string=u'Vínculo Trabalhista')


class HrDependentType(models.Model):
    _name = 'hr.dependent.type'

    name = fields.Char(string=u'Grau de parentesco')
    code = fields.Integer(string=u'Código')
