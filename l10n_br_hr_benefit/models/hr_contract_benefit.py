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

    # Done: Display name
    # Done: Inativar o registro cado a data final seja atingida.
    # TODO: Verificar a necesidade de criação de botões
    #  para inativação pelo gerente
    # TODO: Intervalo de datas
    #       Fazer via python para ver se não coincide no memso intevalo de datas
    # TODO: Criar campo para anexar comprovantes
    # TODO: Criar estado e fluxo de aprovação
    # TODO: Criar wizard para geração apuração de compentencias.
    # TODO: Criar cron para gerar as competências automaticamente;

    name = fields.Char(
        compute='_compute_benefit_name'
    )
    benefit_type_id = fields.Many2one(
        comodel_name='hr.benefit.type',
        string='Tipo Benefício',
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
    active = fields.Boolean(
        string='Ativo',
        default=True,
        readonly=True,
    )


    @api.one
    @api.constrains('date_stop')
    def _check_date_stop_active(self):
        today = fields.Date.today()
        if self.date_stop and self.date_stop <= today:
            self.active = False

    @api.multi
    @api.depends('benefit_type_id', 'beneficiary_id', 'date_start', 'date_stop')
    def _compute_benefit_name(self):
        for record in self:
            if not record.beneficiary_id or \
                    not record.benefit_type_id:
                record.name = 'Novo'
                continue
            name = '%s - %s' % (
                record.beneficiary_id.name or '',
                record.benefit_type_id.name or '')
            if record.date_start and not record.date_stop:
                name += ' (a partir de %s)' % record.date_start
            elif record.date_start and record.date_stop:
                name += ' (de %s até %s)' % (record.date_start,
                                             record.date_stop)
            record.name = name
