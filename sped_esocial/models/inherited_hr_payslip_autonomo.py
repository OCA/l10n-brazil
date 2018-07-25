# -*- coding: utf-8 -*-
# Copyright 2018 ABGF - http://www.abgf.gov.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import _, api, models, fields
from openerp.exceptions import Warning

class HrPaylisp(models.Model):
    _inherit = "hr.payslip.autonomo"

    sped_s2399 = fields.Many2one(
        string='Registro SPED S-2399',
        comodel_name='sped.hr.rescisao.autonomo',
    )

    mtv_deslig = fields.Many2one(
        string='Motivo Término',
        comodel_name='sped.motivo_desligamento',
        help="e-Social: S-2399 - mtvDeslig"
    )

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

    @api.multi
    def create_sped_intermediario_desligamento(self):
        """
        Criar o registro intermediário para o desligamento
        de contrato de trabalho sem vinculo
        """
        for record in self:
            if record.contract_id.evento_esocial == 's2200':
                raise Warning(
                    _('Categoria inválida para rescisao de autonomo.'))

            elif record.contract_id.evento_esocial == 's2300':
                desligamento_id = \
                    self.env['sped.hr.rescisao.autonomo'].create({
                    'sped_hr_rescisao_id': self.id
                })
                record.sped_s2399 = desligamento_id

        return desligamento_id

    @api.multi
    def button_gerar_registro(self):
        """
        Cria o registro intermediario da rescisao e em seguida gera o
        registro do esocial redirecionando o usuario para o registro criado
        """

        # Criar o registro intermediario sped.hr.rescisao.autonomo
        desligamento_id = self.create_sped_intermediario_desligamento()

        sped_registro = desligamento_id.create_sped_registro()

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sped.registro',
            'res_id': sped_registro.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'nodestroy': True,
            'context': self.env.context,
        }
