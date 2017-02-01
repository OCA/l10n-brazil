# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia - Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp
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
    _inherit = 'sped.base'
    _name = 'sped.aliquota.simples.teto'
    _rec_name = 'nome'
    _order = 'valor'

    valor = fields.Monetary('Valor do teto do SIMPLES Nacional', required=True, index=True)
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
    _inherit = 'sped.base'
    _name = 'sped.aliquota.simples.aliquota'
    _rec_name = 'al_simples'
    _order = 'anexo_id, teto_id'

    anexo_id = fields.Many2one('sped.aliquota.simples.anexo', 'Anexo', required=True, ondelete='cascade')
    teto_id = fields.Many2one('sped.aliquota.simples.teto', 'Teto', required=True, ondelete='cascade')
    al_simples = fields.Monetary('SIMPLES', digits=(5, 2), currency_field='currency_aliquota_id')
    al_irpj = fields.Monetary('IRPJ', digits=(5, 2), currency_field='currency_aliquota_id')
    al_csll = fields.Monetary('CSLL', digits=(5, 2), currency_field='currency_aliquota_id')
    al_cofins = fields.Monetary('COFINS', digits=(5, 2), currency_field='currency_aliquota_id')
    al_pis = fields.Monetary('PIS', digits=(5, 2), currency_field='currency_aliquota_id')
    al_cpp = fields.Monetary('CPP', digits=(5, 2), currency_field='currency_aliquota_id')
    al_icms = fields.Monetary('ICMS', digits=(5, 2), currency_field='currency_aliquota_id')
    al_iss = fields.Monetary('ISS', digits=(5, 2), currency_field='currency_aliquota_id')
