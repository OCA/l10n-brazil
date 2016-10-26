# -*- coding: utf-8 -*-
# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api

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


class HrContractLaborBondType(models.Model):
    _name = 'hr.contract.labor.bond.type'

    name = fields.Char(string='Labor bond')


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
    salary_unit = fields.Selection(string='Salary Unity',
                                   selection=[
                                       ('month', 'Per Month'),
                                       ('hour', 'Per Hour')])
    weekly_hours = fields.Float(string='Weekly hours')
    monthly_hours = fields.Float(string='Monthly hours')
    trade_union = fields.Char(string='Trade union')
    trade_union_cnpj = fields.Char(string='Trade union CNPJ')
    trade_union_entity_code = fields.Char(string='Trade union entity code')
    month_base_date = fields.Selection(string='Base date month',
                                       selection=MONTHS)
    discount_trade_union_contribution = fields.Boolean(
        string='Discount trade union contribution in admission')



