# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _


class HrContractSalaryRule(models.Model):

    _name = 'hr.contract.salary.rule'
    _description = 'Rubricas especificas'

    contract_id = fields.Many2one(
        comodel_name="hr.contract",
        string="Contrato",
    )
    rule_id = fields.Many2one(
        comodel_name="hr.salary.rule",
        required=True,
        string=u"Rúbrica",
    )
    date_start = fields.Date(
        string=u"Data de início",
        required=True
    )
    date_stop = fields.Date(
        string=u"Data Final",
    )
    specific_quantity = fields.Float(
        string=u"Quandidade especifica",
    )
    specific_percentual = fields.Float(
        string=u"Percentual especifico",
        default=100.00,
    )
    specific_amount = fields.Float(
        string=u"Valor especifico",
    )
