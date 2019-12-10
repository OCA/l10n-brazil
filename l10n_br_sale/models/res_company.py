# Copyright (C) 2014  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    sale_fiscal_category_id = fields.Many2one(
        "l10n_br_account.fiscal.category",
        u"Categoria Fiscal Padrão de Vendas",
        domain="[('journal_type', '=', 'sale')]",
    )
