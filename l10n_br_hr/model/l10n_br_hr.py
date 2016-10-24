# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields


class L10nBrHrCbo(models.Model):
    _name = "l10n_br_hr.cbo"
    _description = "Brazilian Classification of Occupation"

    code = fields.Char('Code', required=True)
    name = fields.Char('Name', size=255, required=True, translate=True)


class HrDeficiency(models.Model):
    _name = 'hr.deficiency'

    name = fields.Char(string='Deficiency')
    employee_ids = fields.Many2many(string="Employees",
                                    comodel_name='hr.employee')


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
    code = fields.Integer(string='Code')
