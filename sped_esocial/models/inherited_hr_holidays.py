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
    esocial_evento_afastamento_id = fields.Many2one(
        string='Evento e-Social',
        comodel_name='sped.motivo_afastamento',
        related='holiday_status_id.esocial_evento_afastamento_id',
        store=True,
    )
    situacao_esocial = fields.Selection(
        selection=[
            ('1', 'Precisa Transmitir'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
        ],
        string='Situação no e-Social',
        related='sped_esocial_afastamento_id.situacao_esocial_afastamento',
        readonly=True,
    )
    situacao_esocial_encerramento = fields.Selection(
        selection=[
            ('1', 'Precisa Transmitir'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
        ],
        string='Encerramento Afastamento e-Social',
        related='sped_esocial_afastamento_id.'
                'situacao_esocial_afastamento_encerramento',
        readonly=True,
    )
    observacao = fields.Text(
        string='Observação',
        size=255,
    )

    @api.multi
    def encerrar_afastamento(self):
        pass

    @api.constrains('observacao')
    def _check_observacao_obrigatoria(self):
        """
        Verificar se o tipo de afastamento do e-Social exige uma observação
        """
        afastamento_codigo = self.holiday_status_id.esocial_evento_afastamento_id
        if afastamento_codigo:
            if afastamento_codigo.codigo == '21' and not self.observacao:
                raise ValidationError(
                    "Para este tipo de afastamento é obrigatório detalhar o "
                    "afastamento no campo 'observação'!"
                )

    @api.model
    def create(self, vals):
        self.check_dias_afastamento(vals)
        res = super(HrHolidays, self).create(vals)

        return res

    @api.multi
    def holidays_validar_criar_intermediario(self):
        if self.tipo == 'ferias':
            return self._gerar_intermediario_apos_aprovacao()
        else:
            return self.holidays_first_validate()

    @api.multi
    def holidays_validacao_dupla_criar_intermediario(self):
        return self._gerar_intermediario_apos_aprovacao()

    def _gerar_intermediario_apos_aprovacao(self):
        res = self.holidays_validate()
        if res:
            self._gerar_tabela_intermediaria()
        return res

    def check_dias_afastamento(self, vals):
        holidays_status_id = self.env['hr.holidays.status'].browse(
            vals['holiday_status_id'])
        if holidays_status_id.esocial_evento_afastamento_id:
            if holidays_status_id.esocial_evento_afastamento_id.codigo == '15':
                self.valida_dias_inicio_ferias(vals)

    def valida_dias_inicio_ferias(self, vals):
        data_atual = fields.Datetime.from_string(fields.Datetime.now())
        data_inicio = fields.Datetime.from_string(vals['data_inicio'])
        if (data_inicio - data_atual).days > 60:
            raise ValidationError(
                "O inicío do afastamento por gozo de férias não pode ser "
                "maior que 60 dias da data atual!"
            )

    # def valida_dias_afastamento(self, vals):
    #     data_atual = fields.Datetime.from_string(fields.Datetime.now())
    #     data_inicio = fields.Datetime.from_string(vals['data_inicio'])
    #     data_fim = fields.Datetime.from_string(vals['data_fim'])
    #     if (data_inicio - data_atual).days > 0:
    #         raise ValidationError(
    #             "Este evento de afastamento não "
    #             "pode ter seu início no futuro!"
    #         )
    #     if (data_fim - data_inicio).days > 15:
    #         raise ValidationError(
    #             "Este evento de afastamento não "
    #             "pode ser maior do que 15 dias!"
    #         )

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
