# -*- coding: utf-8 -*-
# Copyright 2017 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, exceptions, fields, models, _

from ..constantes_rh import CATEGORIA_TRABALHADOR


class HrContract(models.Model):
    _inherit = 'hr.contract'

    weekly_hours = fields.Float(
        default=40,
    )

    @api.constrains('weekly_hours')
    def _check_weekly_hours(self):
        if self.weekly_hours < 1:
            raise exceptions.Warning(
                _('A quantidade de horas semanais deve estar entre 1 e 44.'))

    @api.multi
    @api.depends('categoria')
    def _compute_categoria_sefip(self):

        for record in self:
            if record.categoria in ('701', '702', '703'):
                #
                # Autônomo
                #
                record.categoria_sefip = '13'
            elif record.categoria in ('721', '722'):
                #
                # Pró-labore
                #
                record.categoria_sefip = '11'
            elif record.categoria == '103':
                #
                # Aprendiz
                #
                record.categoria_sefip = '07'
            else:
                record.categoria_sefip = '01'

    categoria_sefip = fields.Char(
        compute='_compute_categoria_sefip',
        store=True,
    )

    categoria = fields.Selection(
        selection=CATEGORIA_TRABALHADOR,
        string="Categoria do Contrato",
        required=True,
    )

