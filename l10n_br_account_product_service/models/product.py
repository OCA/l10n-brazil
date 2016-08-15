# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields

from .l10n_br_account_product_service import (
    PRODUCT_FISCAL_TYPE,
    PRODUCT_FISCAL_TYPE_DEFAULT)


class ProductTemplate(models.Model):
    """Inherit class to change default value of fiscal_type field"""
    _inherit = 'product.template'

    fiscal_type = fields.Selection(PRODUCT_FISCAL_TYPE,
                                   u'Tipo Fiscal',
                                   required=True,
                                   default=PRODUCT_FISCAL_TYPE_DEFAULT)
