# -*- coding: utf-8 -*-
# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api
from openerp.addons.l10n_br_base.tools import fiscal
from openerp.exceptions import ValidationError


MONTHS = [
    ('1', 'January'),
    ('2', 'February'),
    ('3', 'March'),
    ('4', 'April'),
    ('5', 'May'),
    ('6', 'June'),
    ('7', 'July'),
    ('8', 'August'),
    ('9', 'September'),
    ('10', 'October'),
    ('11', 'November'),
    ('12', 'December'),
]


class HrContractAdmissionType(models.Model):
    _name = 'hr.contract.admission.type'

    name = fields.Char(string='Admission type')
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


class HrContractLaborBondType(models.Model):
    _name = 'hr.contract.labor.bond.type'

    name = fields.Char(string='Labor bond')
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


class HrContractLaborRegime(models.Model):
    _name = 'hr.contract.labor.regime'

    name = fields.Char(string='Labor regime')
    short_name = fields.Char(string='Short name')

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record['name']
            if record['short_name']:
                name = record['short_name'] + ' - ' + name
            result.append((record['id'], name))
        return result


class HrContractSalaryUnit(models.Model):
    _name = 'hr.contract.salary.unit'

    name = fields.Char(string='Salary unit')
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


class HrContractResignationCause(models.Model):
    _name = 'hr.contract.resignation.cause'

    name = fields.Char(string='Resignation cause')
    code = fields.Char(string='Resignation cause code')
    fgts_withdraw_code = fields.Char(string='FGTS withdrawal code')

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record['name']
            if record['code']:
                name = record['code'] + ' - ' + name
            result.append((record['id'], name))
        return result


class HrContractNoticeTermination(models.Model):
    _name = 'hr.contract.notice.termination'

    name = fields.Char(string='Notice of termination type')


class HrContract(models.Model):
    _inherit = 'hr.contract'

    admission_type_id = fields.Many2one(
        string='Admission type',
        comodel_name='hr.contract.admission.type')
    labor_bond_type_id = fields.Many2one(
        string='Labor bond type',
        comodel_name='hr.contract.labor.bond.type')
    labor_regime_id = fields.Many2one(
        string='Labor regime', comodel_name='hr.contract.labor.regime')
    welfare_policy = fields.Selection(
        string='Welfare policy',
        selection=[
            ('rgps', u'Regime Geral da Previdência Social'),
            ('rpps', u'Regime Próprio da Previdência Social')])
    salary_unit = fields.Many2one(string='Salary Unity',
                                  comodel_name='hr.contract.salary.unit')
    weekly_hours = fields.Float(string='Weekly hours')
    monthly_hours = fields.Float(string='Monthly hours')
    union = fields.Char(string='Union')
    union_cnpj = fields.Char(string='Union CNPJ')
    union_entity_code = fields.Char(string='Union entity code')
    month_base_date = fields.Selection(string='Base date month',
                                       selection=MONTHS)
    discount_union_contribution = fields.Boolean(
        string='Discount union contribution in admission')
    resignation_date = fields.Date(string='Resignation date')
    resignation_cause_id = fields.Many2one(
        comodel_name='hr.contract.resignation.cause',
        string='Resignation cause')
    notice_of_termination_id = fields.Many2one(
        string='Notice of termination type',
        comodel_name='hr.contract.notice.termination'
    )
    notice_of_termination_date = fields.Date(
        string='Notice of termination date')
    notice_of_termination_payment_date = fields.Date(
        string='Notice of termination payment date'
    )
    by_death = fields.Char(string='By death',
                           help='Death certificate/Process/Beneficiary')
    resignation_code = fields.Char(related='resignation_cause_id.code',
                                   invisible=True)

    @api.multi
    @api.constrains('union_cnpj')
    def _validate_union_cnpj(self):
        for record in self:
            if record.union_cnpj:
                if not fiscal.validate_cnpj(record.union_cnpj):
                    raise ValidationError("Invalid union CNPJ!")
