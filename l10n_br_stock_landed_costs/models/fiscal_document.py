# Copyright (C) 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    landed_cost_picking_ids = fields.Many2many(
        comodel_name="stock.picking",
        string="Recebimentos a Ratear",
        domain="[('company_id', '=', company_id), ('state', '=', 'done'),"
        " ('picking_type_code', '=', 'incoming')]",
        help="Recebimentos sobre os quais o custo deste documento (frete,"
        " despesas) será rateado.",
    )

    landed_cost_split_method = fields.Selection(
        selection=[
            ("equal", "Igual"),
            ("by_quantity", "Por quantidade"),
            ("by_current_cost_price", "Por custo atual"),
            ("by_weight", "Por peso"),
            ("by_volume", "Por volume"),
        ],
        string="Método de Rateio",
        default="by_quantity",
    )

    landed_cost_ids = fields.One2many(
        comodel_name="stock.landed.cost",
        inverse_name="fiscal_document_id",
        string="Landed Costs",
    )

    landed_cost_count = fields.Integer(
        compute="_compute_landed_cost_count",
    )

    def _compute_landed_cost_count(self):
        for record in self:
            record.landed_cost_count = len(record.landed_cost_ids)

    def _prepare_landed_cost_line_vals(self, line):
        """Uma linha de custo por linha do documento, pelo valor LÍQUIDO:
        o ICMS creditável do frete (CT-e) vira crédito fiscal e não é
        rateado no estoque (Art. 301 RIR/2018, CPC 16)."""
        self.ensure_one()
        net_amount = line.stock_cost_unit * line.quantity
        return {
            "name": line.name or line.product_id.display_name,
            "product_id": line.product_id.id,
            "price_unit": net_amount,
            "split_method": self.landed_cost_split_method,
        }

    def action_create_landed_cost(self):
        self.ensure_one()
        if not self.landed_cost_picking_ids:
            raise UserError(
                _("Selecione os recebimentos sobre os quais ratear o custo.")
            )
        cost_lines = []
        for line in self.fiscal_line_ids:
            vals = self._prepare_landed_cost_line_vals(line)
            if vals["price_unit"]:
                cost_lines.append((0, 0, vals))
        if not cost_lines:
            raise UserError(
                _(
                    "Nenhuma linha com custo líquido para ratear — verifique"
                    " os valores do documento."
                )
            )
        journal = self.env["account.journal"].search(
            [("company_id", "=", self.company_id.id), ("type", "=", "general")],
            limit=1,
        )
        if not journal:
            raise UserError(
                _("Configure um diário contábil geral para a empresa.")
            )
        landed_cost = self.env["stock.landed.cost"].create(
            {
                "picking_ids": [(6, 0, self.landed_cost_picking_ids.ids)],
                "cost_lines": cost_lines,
                "fiscal_document_id": self.id,
                "company_id": self.company_id.id,
                "account_journal_id": journal.id,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "stock.landed.cost",
            "res_id": landed_cost.id,
            "view_mode": "form",
        }


class StockLandedCost(models.Model):
    _inherit = "stock.landed.cost"

    fiscal_document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Documento Fiscal de Origem",
        help="Documento fiscal (ex.: CT-e de frete) que originou este"
        " landed cost.",
    )
