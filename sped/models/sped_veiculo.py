# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError


class Veiculo(models.Model):
    _description = 'Veículo'
    _name = 'sped.veiculo'
    _order = 'placa'
    _rec_name = 'placa'

    placa = fields.UpperChar('Placa', size=8, required=True, index=True)
    estado_id = fields.Many2one('sped.estado', 'Estado', required=True)
    rntrc = fields.Char('RNTRC', size=20)
    transportadora_id = fields.Many2one('res.partner', 'Transportadora', domain=[['eh_transportadora', '=', True]])
    motorista_id = fields.Many2one('res.partner', 'Motorista', domain=[['tipo_pessoa', '=', 'F']])

    def _valida_veiculo(self):
        valores = {}
        res = {'value': valores}

        if (not self.placa):
            return res

        placa = self.placa.strip().replace('-', '').upper()

        if len(placa) != 7:
            raise ValidationError('Placa inválida! Informe a placa no formato AAA-9999')

        if not (placa[0:3].isalpha() and placa[3:7].isdigit()):
            raise ValidationError('Placa inválida! Informe a placa no formato AAA-9999')

        valores['placa'] = placa[0:3] + '-' + placa[3:7]

        if self.id:
            veiculo_ids = self.search([('placa', '=', self.placa), ('id', '!=', self.id)])
        else:
            veiculo_ids = self.search([('placa', '=', self.placa)])

        if len(veiculo_ids) > 0:
            raise ValidationError('Veículo já cadastrado!')

        return res

    @api.one
    @api.constrains('placa')
    def constrains_veiculo(self):
        self._valida_veiculo()

    @api.onchange('placa')
    def onchange_veiculo(self):
        return self._valida_veiculo()
