# -*- coding: utf-8 -*-
# Copyright (C) 2018  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api


class L10nBrAccountProductCST(models.Model):
    _name = 'l10n_br_account_product.cst'

    code = fields.Char(
        string=u'Código',
        required=True)

    name = fields.Char(
        string=u'Nome',
        required=True)

    tax_group_id = fields.Many2one(
        comodel_name='account.tax.group',
        required=True,
        string=u'Grupo de Impostos')

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
        return [(r.id, u"{0} - {1}".format(r.code, r.name))
                for r in self]
