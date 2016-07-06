# -*- coding: utf-8 -*-
# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class ResCompany(models.Model):
    _inherit = "res.company"

    ambiente_sat = fields.Selection(
        [
            ('homologacao', u'Homologação'),
            ('producao', u'Produção'),
        ],
        string='Ambiente SAT',
        required=True,
        default='homologacao'
    )

    cnpj_software_house = fields.Char(
        string=u'CNPJ software house',
        size=18
    )
