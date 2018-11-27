# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api


class L10nBrAccountProductCest(models.Model):

    _name = 'l10n_br_account_product.cest'

    code = fields.Char(
        string=u'Código',
        size=9)

    name = fields.Char(
        string=u'Nome')

    segment = fields.Char(
        string=u'Segmento',
        size=32)

    item = fields.Char(
        string=u'Item',
        size=4)

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
        return [(r.id,
                u"{0} - {1}".format(r.code, r.name))
                for r in self]
