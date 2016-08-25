# -*- coding: utf-8 -*-
# Copyright (C) 2009  Gabriel C. Stabel
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields
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


class L10nBrAccountProductFiscalCategory(models.Model):
    _name = 'l10n_br_account.product.category'

    fiscal_category_source_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Categoria de Origem')
    fiscal_category_destination_id = fields.Many2one(
        'l10n_br_account.fiscal.category', 'Categoria de Destino')
    product_tmpl_id = fields.Many2one(
        'product.template', 'Produto', ondelete='cascade')
    to_state_id = fields.Many2one(
        'res.country.state', 'Estado Destino')
