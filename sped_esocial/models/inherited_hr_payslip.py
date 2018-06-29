# -*- coding: utf-8 -*-
# Copyright 2018 ABGF - http://www.abgf.gov.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields


class HrPaylisp(models.Model):
    _inherit = "hr.payslip"

    @api.multi
    def hr_verify_sheet(self):
        for holerite in self:
            if holerite.state == 'draft':
                if holerite.tipo_de_folha == 'rescisao':
                    holerite.contract_id.resignation_cause_id = \
                        holerite.mtv_deslig
                    holerite.contract_id.resignation_date = \
                        holerite.data_afastamento
            super(HrPaylisp, holerite).hr_verify_sheet()

    # Campo motificado para utilizar a tabela de campos do e-Social
    # Tabela 19 - Motivos de Desligamento
    mtv_deslig = fields.Many2one(
        string='Motivo Desligamento',
        comodel_name='sped.motivo_desligamento',
        help="e-Social: S-2299 - mtvDeslig"
    )
