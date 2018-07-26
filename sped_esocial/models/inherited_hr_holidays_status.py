# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import ValidationError


class HrHolidaysStatus(models.Model):
    _inherit = 'hr.holidays.status'

    esocial_evento_afastamento_id = fields.Many2one(
        string='Evento e-Social',
        comodel_name='sped.motivo_afastamento',
    )

    @api.constrains('esocial_evento_afastamento_id')
    def _check_evento_afastamento_unico(self):
        if self.esocial_evento_afastamento_id and self.search([
            ('esocial_evento_afastamento_id',
             '=',
             self.esocial_evento_afastamento_id.id),
            ('id', '!=', self.id)
        ]):
            raise ValidationError(
                'Já existe um evento selecionado para o tipo de '
                'afastamento ({}) do e-Social'.format(
                    self.esocial_evento_afastamento_id.nome
                )
            )
