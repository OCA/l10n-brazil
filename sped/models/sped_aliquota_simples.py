# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia - Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AliquotaSIMPLESAnexo(models.Model):
    _description = 'Anexo do SIMPLES Nacional'
    _name = 'sped.aliquota.simples.anexo'
    _rec_name = 'nome'
    _order = 'nome'

    nome = fields.Char('Anexo do SIMPLES Nacional', size=40, index=True)
    aliquota_ids = fields.One2many('sped.aliquota.simples.aliquota', 'anexo_id', 'Alíquotas')

    @api.depends('nome')
    def _check_nome(self):
        for anexo in self:
            if anexo.id:
                anexo_ids = self.search([('nome', '=', anexo.nome), ('id', '!=', anexo.id)])
            else:
                anexo_ids = self.search([('nome', '=', anexo.nome)])

            if anexo_ids:
                raise ValidationError('Anexo já existe na tabela!')

        return res


class AliquotaSIMPLESTeto(models.Model):
    _description = 'Teto do SIMPLES Nacional'
    _name = 'sped.aliquota.simples.teto'
    _rec_name = 'nome'
    _order = 'valor'

    valor = fields.Dinheiro('Valor do teto do SIMPLES Nacional', required=True, index=True)
    nome = fields.Char('Teto do SIMPLES Nacional', size=40, index=True)

    @api.depends('valor')
    def _check_valor(self):
        for teto in self:
            if teto.id:
                teto_ids = self.search([('valor', '=', teto.valor), ('id', '!=', teto.id)])
            else:
                teto_ids = self.search([('valor', '=', teto.valor)])

            if teto_ids:
                raise ValidationError('Teto já existe na tabela!')

        return res


class AliquotaSIMPLESAliquota(models.Model):
    _description = 'Alíquota do SIMPLES Nacional'
    _name = 'sped.aliquota.simples.aliquota'
    _rec_name = 'al_simples'
    _order = 'anexo_id, teto_id'

    anexo_id = fields.Many2one('sped.aliquota.simples.anexo', 'Anexo', required=True, ondelete='cascade')
    teto_id = fields.Many2one('sped.aliquota.simples.teto', 'Teto', required=True, ondelete='cascade')
    al_simples = fields.Porcentagem('SIMPLES')
    al_irpj = fields.Porcentagem('IRPJ')
    al_csll = fields.Porcentagem('CSLL')
    al_cofins = fields.Porcentagem('COFINS')
    al_pis = fields.Porcentagem('PIS')
    al_cpp = fields.Porcentagem('CPP')
    al_icms = fields.Porcentagem('ICMS')
    al_iss = fields.Porcentagem('ISS')
