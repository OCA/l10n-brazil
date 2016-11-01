# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from ..constante_tributaria import *
from pybrasil.produto import valida_ean


class Produto(models.Model):
    _description = 'Produtos e serviços'
    _name = 'cadastro.produto'
    _order = 'codigo, nome'
    _rec_name = 'nome'

    #company_id = fields.Many2one('res.company', string='Empresa', ondelete='restrict')
    nome = fields.NameChar(string='Nome', size=120, index=True)
    codigo = fields.Char(string='Código', size=60, index=True)
    codigo_barras = fields.Char(string='Código de barras', size=14, index=True)
    marca = fields.NameChar(string='Marca', size=60)
    foto = fields.Binary('Foto', attachment=True)

    preco_venda = fields.Unitario('Preço de venda')
    preco_custo = fields.Unitario('Preço de custo')
    peso_bruto = fields.Quantidade('Peso bruto')
    peso_liquido = fields.Quantidade('Peso líquido')

    tipo = fields.Selection(TIPO_PRODUTO_SERVICO, string='Tipo', index=True)

    org_icms = fields.Selection(ORIGEM_MERCADORIA, string='Origem da mercadoria', default='0')

    ncm_id = fields.Many2one('sped.ncm', 'NCM')
    cest_ids = fields.Many2many('sped.cest', related='ncm_id.cest_ids', string='Códigos CEST')
    cest_id = fields.Many2one('sped.cest', 'CEST')
    protocolo_id = fields.Many2one('sped.protocolo.icms', 'Protocolo/Convênio')
    al_ipi_id = fields.Many2one('sped.aliquota.ipi', 'Alíquota de IPI')
    al_pis_cofins_id = fields.Many2one('sped.aliquota.pis.cofins', 'Alíquota de PIS e COFINS')

    servico_id = fields.Many2one('sped.servico', 'Código do serviço')
    nbs_id = fields.Many2one('sped.nbs', 'NBS')

    unidade_id = fields.Many2one('cadastro.unidade', 'Unidade')

    def _valida_codigo_barras(self):
        valores = {}
        res = {'value': valores}

        if self.codigo_barras:
            if (not valida_ean(self.codigo_barras)):
                raise ValidationError('Código de barras inválido!')

            valores['codigo_barras'] = self.codigo_barras

        return res

    @api.one
    @api.constrains('codigo_barras')
    def constrains_codigo_barras(self):
        self._valida_codigo_barras()

    @api.onchange('codigo_barras')
    def onchange_codigo_barras(self):
        return self._valida_codigo_barras()

    @api.onchange('ncm_id')
    def onchange_ncm(self):
        if len(self.ncm_id.cest_ids) == 1:
            return {'value': {'cest_id': self.ncm_ids.cest_ids[0].id}}

        elif len(self.ncm_id.cest_ids) > 1:
            return {'value': {'cest_id': False}}
