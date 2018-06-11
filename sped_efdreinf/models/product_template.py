# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    tp_servico_id = fields.Many2one(
        string='Tab.06-EFD/Reinf (Clas.Serviço)',
        comodel_name='sped.classificacao_servico',
    )