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
    def create_sped_registro(self, intermediario_id, company_id, tipo, registro, evento, ambiente):
        """

        :param intermediario_id:
        :param company_id:
        :param tipo:
        :param registro:
        :param evento:
        :param ambiente:
        :return:
        """
        sped_registro_id = self.env['sped.registro'].create({
            'origem':
                ("hr.payslip,{}".format(
                    intermediario_id.sped_hr_rescisao_id.id)),
            'origem_intermediario':
                ("{},{}".format(intermediario_id._name, intermediario_id.id)),
            'company_id': company_id,
            'tipo': tipo,
            'registro': registro,
            'evento': evento,
            'ambiente': ambiente,
        })

        return sped_registro_id

    @api.multi
    def button_gerar_regitro(self):
        """
        Cria o registro intermediario da rescisao e em seguida gera o
        registro do esocial
        """
        desligamento_id = self.create_sped_intermediario_desligamento()

        registro = 'S-2399'
        evento = 'evtTSVTermino'

        sped_registro = self.create_sped_registro(
            desligamento_id, desligamento_id.sped_hr_rescisao_id.company_id.id,
            'esocial', registro, evento,
            desligamento_id.sped_hr_rescisao_id.company_id.esocial_tpAmb
        )

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
