# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields

from .l10n_br_account_product import (
    PRODUCT_FISCAL_TYPE,
    PRODUCT_FISCAL_TYPE_DEFAULT)

PRODUCT_ORIGIN = [
    ('0', u'0 - Nacional, exceto as indicadas nos códigos 3 a 5'),
    ('1', u'1 - Estrangeira - Importação direta, exceto a indicada no código'
        ' 6'),
    ('2', u'2 - Estrangeira - Adquirida no mercado interno, exceto a indicada'
        u' no código 7'),
    ('3', u'3 - Nacional, mercadoria ou bem com Conteúdo de Importação'
        ' superior a 40% (quarenta por cento)'),
    ('4', u'4 - Nacional, cuja produção tenha sido feita em conformidade com'
        u' os processos produtivos básicos de que tratam o Decreto-Lei'
        u' nº 288/67 e as Leis nºs 8.248/91, 8.387/91, 10.176/01 e 11.484/07'),
    ('5', u'5 - Nacional, mercadoria ou bem com Conteúdo de Importação'
        u' inferior ou igual a 40% (quarenta por cento)'),
    ('6', u'6 - Estrangeira - Importação direta, sem similar nacional,'
        u' constante em lista de Resolução CAMEX'),
    ('7', u'7 - Estrangeira - Adquirida no mercado interno, sem similar'
        u' nacional, constante em lista de Resolução CAMEX'),
    ('8', u'8 - Nacional, mercadoria ou bem com Conteúdo de Importação'
        u' superior a 70%')
]


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    fiscal_type = fields.Selection(
        selection_add=PRODUCT_FISCAL_TYPE,
        default=PRODUCT_FISCAL_TYPE_DEFAULT)

    origin = fields.Selection(
        selection=PRODUCT_ORIGIN,
        string=u'Origem',
        default='0')

    fci = fields.Char(
        string=u'FCI do Produto',
        size=36)

    cest_id = fields.Many2one(
        comodel_name='l10n_br_account_product.cest',
        string=u'CEST')

    service_type_id = fields.Many2one(
        comodel_name='l10n_br_account.service.type',
        string=u'Tipo de Serviço')

    estd_import_taxes_perct = fields.Float(
        related='fiscal_classification_id.estd_import_taxes_perct')

    estd_national_taxes_perct = fields.Float(
        related='fiscal_classification_id.estd_national_taxes_perct')
