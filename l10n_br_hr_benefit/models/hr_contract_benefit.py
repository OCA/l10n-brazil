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

    name = fields.Char(
        compute='_compute_benefit_name'
    )
    benefit_type_id = fields.Many2one(
        comodel_name='hr.benefit.type',
        string='Tipo Benefício'
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

    #  Fazer via python para ver se não coincide no memso intevalo de datas
    # _sql_constraints = [('contract_benefit_uniq',
    #                     'UNIQUE(benefit_type, beneficiary_id, date_start, date_stop)',
    # ...

    @api.multi
    @api.depends('benefit_type_id', 'date_start', 'date_stop')
    def _compute_benefit_name(self):
        for record in self:
            record.name = '%s - %s (%s/%s)' % (
                    record.employee_id.name or 'Colaborador',
                    record.benefit_type_id.name or 'Tipo de benefício',
                    record.date_start or 'Data de inicio',
                    record.date_stop or 'Data fim'
            )
