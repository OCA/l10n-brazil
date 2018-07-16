# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import ValidationError


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    sped_esocial_afastamento_id = fields.Many2one(
        string='Evento e-Social',
        comodel_name='sped.esocial.afastamento.temporario',
    )
    situacao_esocial = fields.Selection(
        selection=[
            ('0', 'Inativa'),
            ('1', 'Ativa'),
            ('2', 'Precisa Atualizar'),
            ('3', 'Aguardando Transmissão'),
            ('9', 'Finalizada'),
        ],
        string='Situação no e-Social',
        related='sped_esocial_afastamento_id.situacao_esocial',
        readonly=True,
    )

    @api.model
    def create(self, vals):
        res = super(HrHolidays, self).create(vals)
        res._gerar_tabela_intermediaria()

        return res

    @api.multi
    def _gerar_tabela_intermediaria(self):
        if self.holiday_status_id.esocial_evento_afastamento_id:
            if not self.sped_esocial_afastamento_id:
                if self.env.user.company_id.eh_empresa_base:
                    matriz = self.env.user.company_id.id
                else:
                    matriz = self.env.user.company_id.matriz.id

                self.sped_esocial_afastamento_id = \
                    self.env['sped.esocial.afastamento.temporario'].create({
                        'company_id': matriz,
                        'hr_holiday_id': self.id,
                    })

            # Processa cada tipo de operação do S-2230
            # O que realmente precisará ser feito é tratado no método do registro intermediário
            self.sped_esocial_afastamento_id.gerar_registro()
