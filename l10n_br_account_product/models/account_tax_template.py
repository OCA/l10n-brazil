# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class AccountTaxTemplate(models.Model):
    """Implement computation method in taxes"""
    _inherit = 'account.tax.template'

    icms_base_type = fields.Selection(
        selection=[('0', 'Margem Valor Agregado (%)'),
                   ('1', 'Pauta (valor)'),
                   ('2', 'Preço Tabelado Máximo (valor)'),
                   ('3', 'Valor da Operação')],
        string=u'Tipo Base ICMS',
        required=True,
        default='0')

    icms_st_base_type = fields.Selection(
        selection=[('0', u'Preço tabelado ou máximo  sugerido'),
                   ('1', u'Lista Negativa (valor)'),
                   ('2', u'Lista Positiva (valor)'),
                   ('3', u'Lista Neutra (valor)'),
                   ('4', u'Margem Valor Agregado (%)'),
                   ('5', u'Pauta (valor)')],
        string=u'Tipo Base ICMS ST',
        required=True,
        default='4')
