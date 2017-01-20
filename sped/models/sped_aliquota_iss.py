# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia - Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from odoo import fields, models
import odoo.addons.decimal_precision as dp


class AliquotaISS(models.Model):
    _description = u'Alíquota do ISS'
    _name = 'sped.aliquota.iss'
    _rec_name = 'al_iss'
    _order = 'servico_id, municipio_id, al_iss'

    servico_id = fields.Many2one(
        'sped.servico',
        string=u'Serviço',
        ondelete='cascade',
        required=True,
    )
    municipio_id = fields.Many2one(
        comodel_name='sped.municipio',
        string=u'Município',
        ondelete='restrict',
        required=True
    )
    al_iss = fields.Float(
        string=u'Alíquota',
        required=True,
        digits=(5, 2),
    )
    codigo = fields.Char(
        string=u'Código específico',
        size=10,
    )
