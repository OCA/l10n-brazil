# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AliquotaSIMPLESAnexo(models.Model):
    _description = u'Anexo do SIMPLES Nacional'
    _name = 'sped.aliquota.simples.anexo'
    _rec_name = 'nome'
    _order = 'nome'

    nome = fields.Char(
        string=u'Anexo do SIMPLES Nacional',
        size=40,
        index=True
    )
    aliquota_ids = fields.One2many(
        comodel_name='sped.aliquota.simples.aliquota',
        inverse_name='anexo_id',
        string=u'Alíquotas'
    )

    @api.depends('nome')
    def _check_nome(self):
        for anexo in self:
            if anexo.id:
                anexo_ids = self.search(
                    [('nome', '=', anexo.nome), ('id', '!=', anexo.id)])
            else:
                anexo_ids = self.search([('nome', '=', anexo.nome)])

            if anexo_ids:
                raise ValidationError(u'Anexo já existe na tabela!')


class AliquotaSIMPLESTeto(models.Model):
    _description = u'Teto do SIMPLES Nacional'
    _inherit = 'sped.base'
    _name = 'sped.aliquota.simples.teto'
    _rec_name = 'nome'
    _order = 'valor'

    valor = fields.Monetary(
        string=u'Valor do teto do SIMPLES Nacional',
        required=True,
        index=True,
    )
    nome = fields.Char(
        string=u'Teto do SIMPLES Nacional',
        size=40,
        index=True,
    )

    @api.depends('valor')
    def _check_valor(self):
        for teto in self:
            if teto.id:
                teto_ids = self.search(
                    [('valor', '=', teto.valor), ('id', '!=', teto.id)])
            else:
                teto_ids = self.search(
                    [('valor', '=', teto.valor)])
            if teto_ids:
                raise ValidationError('Teto já existe na tabela!')


class AliquotaSIMPLESAliquota(models.Model):
    _description = u'Alíquota do SIMPLES Nacional'
    _inherit = 'sped.base'
    _name = 'sped.aliquota.simples.aliquota'
    _rec_name = 'al_simples'
    _order = 'anexo_id, teto_id'

    anexo_id = fields.Many2one(
        comodel_name='sped.aliquota.simples.anexo',
        string=u'Anexo',
        required=True,
        ondelete='cascade',
    )
    teto_id = fields.Many2one(
        comodel_name='sped.aliquota.simples.teto',
        string=u'Teto',
        required=True,
        ondelete='cascade',
    )
    al_simples = fields.Monetary(
        string=u'SIMPLES',
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    al_irpj = fields.Monetary(
        string=u'IRPJ',
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    al_csll = fields.Monetary(
        string=u'CSLL',
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    al_cofins = fields.Monetary(
        string=u'COFINS',
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    al_pis = fields.Monetary(
        string=u'PIS',
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    al_cpp = fields.Monetary(
        string=u'CPP',
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    al_icms = fields.Monetary(
        string=u'ICMS',
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    al_iss = fields.Monetary(
        string=u'ISS',
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
