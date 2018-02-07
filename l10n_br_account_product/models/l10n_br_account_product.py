# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import re

from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError
from openerp.addons import decimal_precision as dp

from openerp.addons.l10n_br_base.tools import fiscal
from openerp.addons.l10n_br_account.models.l10n_br_account import TYPE

PRODUCT_FISCAL_TYPE = [
    ('product', 'Produto')
]

PRODUCT_FISCAL_TYPE_DEFAULT = PRODUCT_FISCAL_TYPE[0][0]

NFE_IND_IE_DEST = [
    ('1', '1 - Contribuinte do ICMS'),
    ('2', '2 - Contribuinte Isento do ICMS'),
    ('9', '9 - Não Contribuinte')
]

NFE_IND_IE_DEST_DEFAULT = NFE_IND_IE_DEST[0][0]


class L10nBrAccountProductCest(models.Model):

    _name = 'l10n_br_account_product.cest'

    code = fields.Char(
        u'Código',
        size=9
    )
    name = fields.Char(
        u'Nome'
    )
    segment = fields.Char(
        u'Segmento',
        size=32
    )
    item = fields.Char(
        u'Item',
        size=4
    )

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    @api.multi
    def name_get(self):
        result = []
        for cest in self:
            name = cest.code + ' - ' + cest.name
            result.append((cest.id, name))
        return result
