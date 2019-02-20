# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models
from openerp.addons.l10n_br_hr_payroll.models.hr_payslip import TIPO_DE_FOLHA


class HrContractSalaryRule(models.Model):

    _name = 'hr.contract.salary.rule'
    _description = 'Rubricas especificas'
    _order = "contract_id,date_start DESC,date_stop DESC,rule_id"

    contract_id = fields.Many2one(
        comodel_name="hr.contract",
        string="Contrato",
    )
    rule_id = fields.Many2one(
        comodel_name="hr.salary.rule",
        required=True,
        string=u"Rúbrica",
    )
    tipo_holerite = fields.Selection(
        string="Tipo de Holerite",
        selection=TIPO_DE_FOLHA,
        selection_add=[('all', 'Todos')],
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
        default=1.0,
    )
    specific_percentual = fields.Float(
        string=u"Percentual especifico",
        default=100.00,
    )
    specific_amount = fields.Float(
        string=u"Valor especifico",
    )
    partner_id = fields.Many2one(
        string=u'Beneficiário',
        comodel_name='res.partner',
    )
