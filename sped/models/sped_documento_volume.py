# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from odoo import fields, models
import odoo.addons.decimal_precision as dp


class DocumentoVolume(models.Model):
    _description = 'Volume do Documento Fiscal'
    _name = 'sped.documento.volume'
    # _order = 'emissao, modelo, data_emissao desc, serie, numero'
    # _rec_name = 'numero'

    documento_id = fields.Many2one(
        comodel_name='sped.documento',
        string=u'Documento',
        ondelete='cascade',
        required=True,
    )
    especie = fields.Char(
        string=u'Espécie',
        size=60
    )
    marca = fields.Char(
        string=u'Marca',
        size=60
    )
    numero = fields.Char(
        string=u'Número', size=60
    )
    quantidade = fields.Float(
        string=u'Quantidade',
        digits=dp.get_precision('SPED - Quantidade')
    )
    peso_liquido = fields.Float(
        string=u'Peso líquido',
        digits=dp.get_precision('SPED - Peso')
    )
    peso_bruto = fields.Float(
        string=u'Peso bruto',
        digits=dp.get_precision('SPED - Peso')
    )
