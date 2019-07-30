# -*- coding: utf-8 -*-
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from openerp import api, fields, models, _


class HrContractBenefit(models.Model):
    _name = b'hr.contract.benefit'
    _inherit = ['mail.thread']

    _description = 'Benefícios'

    # TODO: Display name
    name = fields.Char() # Criar cálculo para o nome com as datas
    benefit_type = fields.Many2one(
        comdel_name='hr.benefit.type',
        string='Tipo de Benefício',
        index=True,
    )
    date_start = fields.Date(
        string='Date Start',
        index=True,
    )
    date_stop = fields.Date(
        string='Date Start',
        index=True,
    )
    contract_id = fields.Many2one(
        comodel_name='hr.contract',
        required=True,
        index=True,
        string='Contrato'
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        related='contract_id.employee_id',
        readonly=True,
        index=True,
        string='Colaborador'
    )
    beneficiary_id = fields.Many2one(
        comodel_name='res.partner',
        index=True,
        string='Beneficiário',
    )
    # amount = fields.Many2one(
    #
    # )

    #  TODO: Fazer via python para ver se não coincide no
    #   memso intevalo de datas
    # _sql_constraints = [('contract_benefit_uniq',
    #                     'UNIQUE(benefit_type, beneficiary_id, date_start, date_stop)',
    # ...
