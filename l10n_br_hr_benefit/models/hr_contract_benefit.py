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
    # Done: Intervalo de datas
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
        required=True,
    )
    date_start = fields.Date(
        string='Date Start',
        index=True,
    )
    date_stop = fields.Date(
        string='Date Stop',
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
        required=True,
        string='Beneficiário',
    )
    active = fields.Boolean(
        string='Ativo',
        default=True,
        readonly=True,
    )

    @api.one
    @api.constrains('date_start', 'date_stop')
    def _check_valid_date_interval(self):
        if self.date_stop and self.date_stop < self.date_start:
            raise Warning(
                _('Data final menor que data inicial'))

    @api.one
    @api.constrains('date_stop')
    def _check_date_stop_active(self):
        today = fields.Date.today()
        if self.date_stop and self.date_stop <= today:
            self.active = False

    @api.one
    @api.constrains("date_start", "date_stop", "benefit_type_id",
                    "beneficiary_id")
    def _check_dates(self):
        domain = [
            ('id', '!=', self.id),
            ('benefit_type_id', '=', self.benefit_type_id.id),
            ('beneficiary_id', '=', self.beneficiary_id.id),
            ('date_start', '<=', self.date_start),
            '|',
            ('date_stop', '=', False),
            ('date_stop', '>=', self.date_start),
        ]
        overlap = self.search(domain)
        if overlap:
            raise Warning(
                _('Já existe um tipo de benefício '
                  'com o mesmo nome e com datas'
                  ' que sobrepõem essa'))

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

    @api.model
    def _agrupar_beneficios(self):

        result = {}

        contract_model = self.env['hr.contract']
        benefit_type_model = self.env['hr.benefit.type']

        sql = """SELECT contract_id, benefit_type_id, array_agg(id)
            FROM hr_contract_benefit
            WHERE active='t'
            GROUP BY contract_id, benefit_type_id"""
        self.env.cr.execute(sql)

        for contract_id, benefit_type_id, \
            benefit_ids in self.env.cr.fetchall():
            contract = contract_model.browse(contract_id)
            benefit_type = benefit_type_model.browse(benefit_type_id)

            benefits = self.search(
                [('id', 'in', benefit_ids)]
            )

            result[(contract, benefit_type)] = benefits

        return result

    @api.multi
    def gerar_prestacao_contas(self, period_id=False):
        if not period_id:
            period_id = self.env['account.period'].find()

        beneficios_agrupados = self._agrupar_beneficios()

        result = self.env['hr.contract.benefit.line']

        for contract_id, benefit_type_id in beneficios_agrupados:
            result |= self.env['hr.contract.benefit.line'].create({
                'benefit_type_id': benefit_type_id.id,
                'contract_id': contract_id.id,
                'period_id': period_id.id,
                'beneficiary_ids': [(6, 0, beneficios_agrupados[
                    (contract_id, benefit_type_id)
                ].mapped('beneficiary_id').ids)],
                'state': 'todo',
            })

        return result
