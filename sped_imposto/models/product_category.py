# -*- coding: utf-8 -*-
# Copyright 2018 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class ProductCategory(models.Model):

    _inherit = 'product.category'

    code = fields.Char(
        string=u'Código'
    )
    protocolo_ids = fields.Many2many(
        comodel_name='sped.protocolo.icms',
        string='Protocolo/Convênio',
        groups='sped_imposto.GRUPO_FISCAL_LEITURA',
    )

