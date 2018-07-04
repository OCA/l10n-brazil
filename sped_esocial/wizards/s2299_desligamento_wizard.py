# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields


class S2299DesligamentoWizard(models.TransientModel):
    _name = 's2299.desligamento.wizard'

    pens_alim = fields.Selection(
        string='Pensão Alimentícia',
        selection=[
            ('0', 'Não existe Pensão'),
            ('1', 'Percentual de Pensão'),
            ('2', 'Valor de Pensão'),
            ('3', 'Percentual e Valor de Pensão'),
        ],
        required=True,
        default='0',
        help='e-Social: S2299 - pensAlim',
    )
    pensao_id = fields.One2many(
        string='Pensões a Pagar',
        comodel_name='s2299.desligamento.pensao.wizard',
        inverse_name='wizard_id',
    )

    @api.multi
    def create_s2299_desligamento(self):
        """
        Criar o registro intermediário para o desligamento
        de contrato de trabalho
        :return:
        """
        vals = {
            'sped_hr_rescisao_id': self.env.context['active_id'],
            'pens_alim': self.pens_alim,
        }
        if self.pens_alim != 0:
            vals['pagamento_pensao'] = True
            porcentagem = 0.0
            valor = 0.0

            for pensao in self.pensao_id:
                porcentagem += pensao.perc_aliment
                valor += pensao.vr_alim

            vals['perc_aliment'] = porcentagem
            vals['vr_alim'] = valor

        s2299_desligamento = self.env['sped.hr.rescisao'].create(vals)

        return s2299_desligamento

    @api.multi
    def create_sped_registro(self, intermediario_id, company_id, tipo, registro, evento, ambiente):
        sped_registro_id = self.env['sped.registro'].create({
            'origem': ("sped.hr.rescisao,{}".format(intermediario_id)),
            'company_id': company_id,
            'tipo': tipo,
            'registro': registro,
            'evento': evento,
            'ambiente': ambiente,
        })

        return sped_registro_id

    @api.multi
    def button_transmitir(self):
        s2299_desligamento_id = self.create_s2299_desligamento()
        sped_registro = self.create_sped_registro(
            s2299_desligamento_id.id,
            s2299_desligamento_id.sped_hr_rescisao_id.company_id.id,
            'esocial',
            'S-2299',
            'evtDeslig',
            s2299_desligamento_id.sped_hr_rescisao_id.company_id.esocial_tpAmb
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


class S229DesligamentoPensaoWizard(models.TransientModel):
    _name = 's2299.desligamento.pensao.wizard'

    perc_aliment = fields.Float(
        string='Percentual da Pensão',
        help='e-Social: S2299 - percAliment',
    )
    vr_alim = fields.Float(
        string='Valor da Pensão',
        help='e-Social: S2299 - vrAlim',
    )
    wizard_id = fields.Many2one(
        comodel_name='s2299.desligamento.wizard',
    )
