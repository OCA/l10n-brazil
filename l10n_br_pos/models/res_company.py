# -*- coding: utf-8 -*-
# See README.rst file on addon root folder for license details

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
