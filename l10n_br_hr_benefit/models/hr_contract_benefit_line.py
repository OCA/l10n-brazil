# -*- coding: utf-8 -*-
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from openerp import api, fields, models, _


class HrContractBenefitLine(models.Model):

    _name = b'hr.contract.benefit.line'
    _inherit = ['mail.thread']
    _description = 'Prestação de contas'

    # TODO: Display name
    name = fields.Char()
    benefit_type_id = fields.Many2one(
        comodel_name='hr.benefit.type',
        required=True,
        string='Tipo Benefício'
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
        string='Colaborador',
    )
    period_id = fields.Many2one(
        comodel_name='account.period',
        string='Competência',
        index=True,
    )
    date_start = fields.Date(
        string='Date Start',
        index=True,
    )
    date_stop = fields.Date(
        string='Date Stop',
        index=True,
    )
    beneficiary_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Beneficiários',
    )
    amount_base = fields.Float(
        string='Valor Comprovado',
        index=True,
    )
    amount_benefit = fields.Float(
        string='Valor Apurado',
        index=True,
    )
    state = fields.Selection(
        selection=[
            ('todo', 'Aguardando Comprovante'),
            ('waiting', 'Enviado'),
            ('validated', 'Apurado'),
            ('exception', 'Negado'),
            ('cancel', 'Cancelado'),
        ],
        string='Situação',
        index=True,
    )
    attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        relation='hr_contract_benefit_line_att_rel',
        column1='benefit_line_id',
        column2='attachment_id',
        string='Attachments'
    )
    is_payroll_processed = fields.Boolean(
        string='Lançado em folha de pagamento',
        readonly=True,
    )
    # TODO: Colocar a folha que foi processado e tornar o campo acima calculado

