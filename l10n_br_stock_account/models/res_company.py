# -*- coding: utf-8 -*-
# Copyright (C) 2011  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    stock_fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category',
        u'Categoria Fiscal Padrão Estoque')
    stock_in_fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category',
        u'Categoria Fiscal Padrão de Entrada',
        domain="[('journal_type', 'in', ('sale_refund', 'purchase')), "
        "('fiscal_type', '=', 'product'), ('type', '=', 'input')]")
    stock_out_fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category',
        u'Categoria Fiscal Padrão Saída',
        domain="[('journal_type', 'in', ('purchase_refund', 'sale')), "
        "('fiscal_type', '=', 'product'), ('type', '=', 'output')]")
