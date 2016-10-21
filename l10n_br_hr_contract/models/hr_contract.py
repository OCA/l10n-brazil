# -*- coding: utf-8 -*-
# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api


class HrContractAdmissionType(models.Model):
    _name = 'hr.contract.admission.type'

    name = fields.Char(string=u'Tipo de Admissão')


class HrContractLaborBondType(models.Model):
    _name = 'hr.contract.labor.bond.type'

    name = fields.Char(string=u'Vínculo trabalhista')


class HrContractLaborRegime(models.Model):
    _name = 'hr.contract.labor.regime'

    name = fields.Char(string='Regime Trabalhista')


class HrContract(models.Model):
    _inherit = 'hr.contract'

    admission_type_id = fields.Many2one(
        string=u'Tipo de Admissão',
        comodel_name='hr.contract.admission.type')
    labor_bond_type_id = fields.Many2one(
        string=u'Tipo de vínculo trabalhista',
        comodel_name='hr.contract.labor.bond.type')

