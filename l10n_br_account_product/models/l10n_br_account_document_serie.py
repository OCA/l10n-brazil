# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields

from .l10n_br_account_product import (
    PRODUCT_FISCAL_TYPE,
    PRODUCT_FISCAL_TYPE_DEFAULT,
)


class L10nBrAccountDocumentSerie(models.Model):
    _inherit = 'l10n_br_account.document.serie'

    fiscal_type = fields.Selection(
        selection=PRODUCT_FISCAL_TYPE,
        string='Tipo Fiscal',
        required=True,
        default=PRODUCT_FISCAL_TYPE_DEFAULT)
