# -*- coding: utf-8 -*-
# Copyright (C) 2009  Gabriel C. Stabel
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class L10nBrAccountProductFiscalCategory(models.Model):
    _name = 'l10n_br_account.product.category'

    fiscal_category_source_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.category',
        string=u'Categoria de Origem')

    fiscal_category_destination_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.category',
        string=u'Categoria de Destino')

    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string=u'Produto',
        ondelete='cascade')

    to_state_id = fields.Many2one(
        comodel_name='res.country.state',
        string=u'Estado Destino')
