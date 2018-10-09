# -*- coding: utf-8 -*-
# Copyright 2017 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, exceptions, fields, models, _

from ..constantes_rh import CATEGORIA_TRABALHADOR, CATEGORIA_TRABALHADOR_SEFIP


class HrContract(models.Model):
    _inherit = 'hr.contract'

    weekly_hours = fields.Float(
        default=40,
    )

    codigo_guia_darf = fields.Char(
        string='Código DARF',
        help='Código para geração da Guia DARF',
        default='0561',
    )

    @api.constrains('weekly_hours')
    def _check_weekly_hours(self):
        if self.weekly_hours < 1:
            raise exceptions.Warning(
                _('A quantidade de horas semanais deve estar entre 1 e 44.'))
