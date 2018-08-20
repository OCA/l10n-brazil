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
    def create_sped_intermediario_desligamento(self):
        """
        Criar o registro intermediário para o desligamento
        de contrato de trabalho
        :return:
        """
        # Identificar qual categoria de contrato para definir o registro sped
        payslip = self.env['hr.payslip'].browse(self.env.context['active_id'])

        vals = {
            'company_id': payslip.company_id.id,
            'sped_hr_rescisao_id': payslip.id,
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

        desligamento_id = False
        if payslip.contract_id.evento_esocial == 's2200':
            desligamento_id = self.env['sped.hr.rescisao'].create(vals)
            payslip.sped_s2299 = desligamento_id

        elif payslip.contract_id.evento_esocial == 's2300':
            desligamento_id = self.env['sped.hr.rescisao.autonomo'].create(vals)
            payslip.sped_s2399 = desligamento_id

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
    def button_transmitir(self):
        """
        Cria o registro intermediario da rescisao e em seguida gera o
        registro do esocial
        """
        desligamento_id = self.create_sped_intermediario_desligamento()
        desligamento_id.gerar_registro()

        # if desligamento_id.sped_hr_rescisao_id.contract_id.evento_esocial == 's2300':
        #     registro = 'S-2399'
        #     evento = 'evtTSVTermino'
        # else:
        #     registro = 'S-2299'
        #     evento = 'evtDeslig'
        #
        # sped_registro = self.create_sped_registro(
        #     desligamento_id, desligamento_id.sped_hr_rescisao_id.company_id.id,
        #     'esocial', registro, evento,
        #     desligamento_id.sped_hr_rescisao_id.company_id.esocial_tpAmb
        # )
        #
        # desligamento_id.sped_s2299_registro_inclusao = sped_registro
        #
        # return {
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'res_model': 'sped.registro',
        #     'res_id': sped_registro.id,
        #     'type': 'ir.actions.act_window',
        #     'target': 'current',
        #     'nodestroy': True,
        #     'context': self.env.context,
        # }


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
