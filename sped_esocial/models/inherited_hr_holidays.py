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
        ondelete='cascade',
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
        self.check_dias_afastamento(vals)
        res = super(HrHolidays, self).create(vals)
        res._gerar_tabela_intermediaria()

        return res

    def check_dias_afastamento(self, vals):
        holidays_status_id = self.env['hr.holidays.status'].browse(
            vals['holiday_status_id'])
        if holidays_status_id.esocial_evento_afastamento_id.codigo != '15':
            self.valida_dias_afastamento(vals)
        else:
            self.valida_dias_inicio_ferias(vals)

    def valida_dias_inicio_ferias(self, vals):
        data_atual = fields.Datetime.from_string(fields.Datetime.now())
        data_inicio = fields.Datetime.from_string(vals['data_inicio'])
        if (data_inicio - data_atual).days > 60:
            raise ValidationError(
                "O inicío do afastamento por gozo de férias não pode ser "
                "maior que 60 dias da data atual!"
            )

    def valida_dias_afastamento(self, vals):
        data_inicio = fields.Datetime.from_string(vals['data_inicio'])
        data_fim = fields.Datetime.from_string(vals['data_fim'])
        if (data_fim - data_inicio).days > 15:
            raise ValidationError(
                "Este evento de afastamento não "
                "pode ser maior do que 15 dias!"
            )

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
