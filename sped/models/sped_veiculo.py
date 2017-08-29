# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SpedVeiculo(models.Model):
    _name = b'sped.veiculo'
    _description = 'Veículos'
    _order = 'placa'
    _rec_name = 'placa'

    placa = fields.Char(
        string='Placa',
        size=8,
        required=True,
        index=True,
    )
    estado_id = fields.Many2one(
        comodel_name='sped.estado',
        string='Estado',
        required=True,
    )
    rntrc = fields.Char(
        string='RNTRC',
        size=20,
    )
    transportadora_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Transportadora',
        domain=[['eh_transportadora', '=', True]],
    )
    motorista_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Motorista',
        domain=[['tipo_pessoa', '=', 'F']]
    )

    def _valida_placa(self):
        self.ensure_one()

        res = {}
        valores = {}
        res['value'] = valores

        placa = self.placa.strip().replace(
            '-', '').replace(' ', '').replace(
            ' ', '').upper()

        if len(placa) != 7:
            raise ValidationError(
                'Placa inválida! Informe a placa no formato AAA-9999')

        if not (placa[0:3].isalpha() and placa[3:7].isdigit()):
            raise ValidationError(
                'Placa inválida! Informe a placa no formato AAA-9999')

        valores['placa'] = placa[0:3] + '-' + placa[3:7]

        if self.id:
            veiculo_ids = self.search(
                [('placa', '=', self.placa), ('id', '!=', self.id)])
        else:
            veiculo_ids = self.search([('placa', '=', self.placa)])

        if len(veiculo_ids) > 0:
            raise ValidationError('Veículo já cadastrado!')

        return res

    @api.constrains('placa')
    def _check_placa(self):
        for veiculo in self:
            veiculo._valida_placa()

    @api.onchange('placa')
    def _onchange_placa(self):
        return self._valida_placa()
