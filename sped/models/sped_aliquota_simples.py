# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia - Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#




from odoo import api, fields, models
import odoo.addons.decimal_precision as dp
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

        return res


class AliquotaSIMPLESTeto(models.Model):
    _description = u'Teto do SIMPLES Nacional'
    _name = 'sped.aliquota.simples.teto'
    _rec_name = 'nome'
    _order = 'valor'

    #
    # Para todos os valores de teto de alíquota do SIMPLES, a moeda é sempre o
    # Real BRL
    #
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string=u'Moeda',
        default=lambda self: self.env.ref('base.BRL').id,
    )
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

        return res


class AliquotaSIMPLESAliquota(models.Model):
    _description = u'Alíquota do SIMPLES Nacional'
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
    al_simples = fields.Float(
        string=u'SIMPLES',
        digits=(5, 2),
    )
    al_irpj = fields.Float(
        string=u'IRPJ',
        digits=(5, 2),
    )
    al_csll = fields.Float(
        string=u'CSLL',
        digits=(5, 2),
    )
    al_cofins = fields.Float(
        string=u'COFINS',
        digits=(5, 2),
    )
    al_pis = fields.Float(
        string=u'PIS',
        digits=(5, 2)
    )
    al_cpp = fields.Float(
        string=u'CPP',
        digits=(5, 2)
    )
    al_icms = fields.Float(
        string=u'ICMS',
        digits=(5, 2)
    )
    al_iss = fields.Float(
        string=u'ISS',
        digits=(5, 2)
    )
