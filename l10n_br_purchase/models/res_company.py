# -*- coding: utf-8 -*-
# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    purchase_fiscal_category_id = fields.Many2one(
        'l10n_br_account.fiscal.category',
        u'Categoria Fiscal Padrão Compras',
        domain="[('journal_type', '=', 'purchase')]")
