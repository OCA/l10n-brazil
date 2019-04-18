# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class AccountInvoice(models.Model):
    _inherit = 'product.template'

    codigo_contabil = fields.Char(
        string=u'Código Contábil',
    )
