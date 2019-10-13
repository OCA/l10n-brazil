# -*- coding: utf-8 -*-
# Copyright (C) 2009  Gabriel C. Stabel
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields
from .l10n_br_account import PRODUCT_FISCAL_TYPE, PRODUCT_FISCAL_TYPE_DEFAULT


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    fiscal_category_default_ids = fields.One2many(
        'l10n_br_account.product.category', 'product_tmpl_id',
        u'Categoria de Operação Fiscal Padrões')
    service_type_id = fields.Many2one(
        'l10n_br_account.service.type', u'Tipo de Serviço')
    fiscal_type = fields.Selection(
        PRODUCT_FISCAL_TYPE,
        'Tipo Fiscal',
        default=PRODUCT_FISCAL_TYPE_DEFAULT
    )
