# Copyright 2020 - TODAY, Marcel Savegnago - Escodoo - https://www.escodoo.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
from ...l10n_br_fiscal.constants.fiscal import TAX_FRAMEWORK


class RepairFee(models.Model):
    _name = 'repair.fee'
    _inherit = [_name, 'l10n_br_repair.fiscal.line.mixin']

    # Adapt Mixin's fields
    fiscal_tax_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.tax',
        relation='fiscal_repair_fee_tax_rel',
        column1='document_id',
        column2='fiscal_tax_id',
        string='Fiscal Taxes',
    )

    tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        related='repair_id.company_id.tax_framework',
        string='Tax Framework',
    )

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        related='repair_id.partner_id',
        string='Partner',
    )

    comment_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.comment',
        relation='repair_fee_comment_rel',
        column1='repair_fee_id',
        column2='comment_id',
        string='Comments',
    )

    quantity = fields.Float(
        'Part Quantity',
        related='product_uom_qty',
        depends=['product_uom_qty'],
    )

    uom_id = fields.Many2one(
        related='product_uom',
        depends=['product_uom'],
    )

    company_id = fields.Many2one(
        related='repair_id.company_id',
        store=True,
    )
