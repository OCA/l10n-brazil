# Copyright 2020 - TODAY, Marcel Savegnago - Escodoo - https://www.escodoo.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMove(models.Model):
    _name = "stock.move"
    _inherit = ["l10n_br_repair.fiscal.line.mixin", _name]

    is_repair_line = fields.Boolean(
        compute="_compute_is_repair_line",
        store=True,
    )

    fiscal_tax_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.tax",
        relation="fiscal_repair_line_tax_rel",
        column1="document_id",
        column2="fiscal_tax_id",
        string="Fiscal Taxes",
    )

    tax_framework = fields.Selection(
        related="repair_id.company_id.tax_framework",
        string="Tax Framework",
    )

    ind_final = fields.Selection(related="repair_id.ind_final")

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="repair_line_comment_rel",
        column1="repair_line_id",
        column2="comment_id",
        string="Comments",
    )

    uom_id = fields.Many2one(
        related="product_uom",
        depends=["product_uom"],
    )

    @api.depends("repair_id", "repair_line_type")
    def _compute_is_repair_line(self):
        for move in self:
            move.is_repair_line = bool(move.repair_id and move.repair_line_type)
