# -*- coding: utf-8 -*-
# Copyright 2018 ABGF - Hendrix Costa <hendrix.costa@abgf.gov.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openerp import api, fields, models

_logger = logging.getLogger(__name__)
try:
    from pybrasil.data import formata_data
except ImportError as err:
    _logger.debug = (err)


class L10nBrHrSubstituicao(models.Model):
    _name = 'hr.substituicao'
    _description = u'Substituição de Funcionários'
    _order='data_inicio DESC,data_fim DESC'

    name = fields.Char(
        string='Nome',
        compute='_compute_name',
    )

    department_id = fields.Many2one(
        comodel_name='hr.department',
        string='Departamento',
        domain="[('state', '=', 'ativo')]",
    )

    funcionario_titular = fields.Many2one(
        string='Funcionário Titular',
        comodel_name='hr.employee',
        help='Funcionário Titular oficil do cargo',
    )

    funcionario_substituto = fields.Many2one(
        string='Funcionário Substituto',
        comodel_name='hr.employee',
        help='Funcionário Substituto na ausência do titular',
        domain="[('id','!=',funcionario_titular)]",
    )

    data_inicio = fields.Date(
        string='Data Inicial',
        help='Data de Início da substituição',
    )

    data_fim = fields.Date(
        string='Data Fim',
        help='Data de Fim da substituição',
    )

    holiday_id = fields.Many2one(
        comodel_name='hr.holidays',
        string='Ocorrência',
        help='Ocorrência que originou a substituição',
        ondelete='cascade',
    )

    @api.onchange('department_id')
    def _onchange_department_id(self):
        for record in self:
            record.funcionario_titular = record.department_id.manager_id
            record.funcionario_substituto = \
                record.department_id.manager_substituto_id

    @api.multi
    @api.depends('data_inicio', 'data_fim')
    def _compute_name(self):
        for subs in self:
            if subs.data_inicio and subs.data_fim:
                subs.name = 'Substituição {} {} - {}'.format(
                    subs.department_id.name,
                    formata_data(subs.data_inicio),
                    formata_data(subs.data_fim)
                )
