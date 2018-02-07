# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api


class ImportDeclarationLine(models.Model):
    _name = 'l10n_br_account_product.import.declaration.line'

    import_declaration_id = fields.Many2one(
        'l10n_br_account_product.import.declaration', u'DI',
        ondelete='cascade', select=True)
    sequence = fields.Integer(u'Sequência', default=1, required=True)
    name = fields.Char(u'Adição', size=3, required=True)
    manufacturer_code = fields.Char(
        u'Código do Fabricante', size=60, required=True)
    amount_discount = fields.Float(u'Valor',
                                   digits=dp.get_precision('Account'),
                                   default=0.00)
