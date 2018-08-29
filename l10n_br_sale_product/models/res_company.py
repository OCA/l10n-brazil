# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion                                  #
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    default_ind_pres = fields.Selection([
        ('0', u'Não se aplica (por exemplo,'
              u' Nota Fiscal complementar ou de ajuste)'),
        ('1', u'Operação presencial'),
        ('2', u'Operação não presencial, pela Internet'),
        ('3', u'Operação não presencial, Teleatendimento'),
        ('4', u'NFC-e em operação com entrega em domicílio'),
        ('5', u'Operação presencial, fora do estabelecimento'),
        ('9', u'Operação não presencial, outros'),
    ], u'Tipo de operação',
        help=u'Indicador de presença do comprador no \
            \nestabelecimento comercial no momento \
            \nda operação.')
