# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from openerp import api, fields, models

_logger = logging.getLogger(__name__)


class AdiantamentoDecimoTerceiroWizard(models.TransientModel):
    _name = 'adiantamento.decimo.terceiro.wizard'

    start_period_id = fields.Many2one(
        string=u'Período Inicial',
        comodel_name='account.period',
        domain=[('special', '=', False)],
        required=True,
        default=lambda self: self.env['account.period'].find(
            '{}-01-01'.format(fields.Date.today()[:4])),
    )

    end_period_id = fields.Many2one(
        string=u'Período Final',
        comodel_name='account.period',
        domain=[('special', '=', False)],
        required=True,
        default=lambda self: self.env['account.period'].find(),
    )

    company_ids = fields.Many2many(
        string=u'Empresas',
        comodel_name='res.company',
        required=True,
        default=lambda self: self.env['res.company'].search([]),
    )

    contract_id = fields.Many2many(
        string=u'Contratos',
        comodel_name='hr.contract',
    )

    @api.multi
    @api.onchange('start_period_id')
    def onchange_start_period_id(self):
        if self.start_period_id:
            domain = [
                ('date_stop', '>=', self.start_period_id.date_start),
                ('special', '=', False)
            ]
            return {'domain': {'end_period_id': domain}}

    @api.multi
    @api.onchange('end_period_id', 'company_ids')
    def buscar_contratos(self):
        """
        Buscar contratos dos funcionários que recebem 13º Salário
        """
        for record in self:
            if record.end_period_id and record.company_ids:
                domain = [
                    '|',
                    ('date_end', '>=', record.end_period_id.fiscalyear_id.date_start),
                    ('date_end', '=', False),
                    ('tp_jornada', '=', '1'),
                    ('company_id', 'in', record.company_ids.ids),
                ]

                contract_id = self.env['hr.contract'].search(domain)

                record.contract_id = contract_id

    @api.multi
    def get_relatorio(self):
        for record in self:
            if not record.contract_id:
                raise Warning(
                    "Não existe nenhum contrato selecionado!"
                )
            else:
                return record.env['report'].get_action(
                    self,
                    "l10n_br_contabilidade.report_adiantamento_decimo_terceiro"
                )
