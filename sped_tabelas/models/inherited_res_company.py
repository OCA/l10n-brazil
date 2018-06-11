# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, exceptions


class ResCompany(models.Model):
    _inherit = 'res.company'

    classificacao_tributaria_id = fields.Many2one(
        string='Classificação Tributária',
        comodel_name='sped.classificacao_tributaria'
    )

