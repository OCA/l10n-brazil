# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class ResPartner(models.Model):

    _inherit = 'res.partner'

    tp_lograd = fields.Many2one(
        string=u'Tipo de Logradouro',
        comodel_name='sped.tipo_logradouro',
        default=lambda self: self.env.ref('sped_tabelas.tab20_R'),
    )
