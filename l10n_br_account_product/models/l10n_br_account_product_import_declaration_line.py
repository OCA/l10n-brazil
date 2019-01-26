# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields
from odoo.addons import decimal_precision as dp


class ImportDeclarationLine(models.Model):
    _name = 'l10n_br_account_product.import.declaration.line'

    import_declaration_id = fields.Many2one(
        comodel_name='l10n_br_account_product.import.declaration',
        string=u'DI',
        ondelete='cascade',
        index=True
    )
    sequence = fields.Integer(
        string=u'Sequência',
        default=1,
        required=True
    )
    name = fields.Char(
        string=u'Adição',
        size=3,
        required=True
    )
    manufacturer_code = fields.Char(
        string=u'Código do Fabricante',
        size=60,
        required=True
    )
    amount_discount = fields.Float(
        string=u'Valor',
        digits=dp.get_precision('Account'),
        default=0.00
    )
