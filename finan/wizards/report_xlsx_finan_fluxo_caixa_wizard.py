# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
#    Aristides Caldeira <aristides.caldeira@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from datetime import datetime

from odoo import fields, models, api


class ReportXlsxFinanFluxoCaixaWizard(models.TransientModel):
    _name = b'report.xlsx.finan.fluxo.caixa.wizard'
    _description = 'Relatório de Fluxo de Caixa - Wizard'

    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
        default=lambda self: self.env['sped.empresa']._empresa_ativa('sped.empresa'),
        required=True,
    )
    periodo = fields.Selection(
        string='Período em',
        required=True,
        default='meses',
        selection=[
            ('meses', 'Meses'),
            #('semanas', 'Semanas'),
            ('dias', 'Dias'),
        ],
    )
    data_periodo = fields.Selection(
        selection=[
            ('data_vencimento_util', 'Período Previsto'),
            ('data_credito_debito', 'Período Realizado')
        ],
        string='Período',
        required=True,
        default='data_vencimento_util',
    )
    data_inicial = fields.Date(
        required=True,
        default=datetime.now().strftime('%Y-%m-01'),
    )
    data_final = fields.Date(
        required=True,
        default=datetime.now().strftime('%Y-12-31'),
    )

    @api.multi
    def gera_relatorio(self):
        self.ensure_one()

        return self.env['report'].get_action(
            self,
            report_name='report_xlsx_finan_fluxo_caixa'
        )
