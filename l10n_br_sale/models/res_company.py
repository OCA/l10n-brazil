# Copyright (C) 2014  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, fields, models


class Company(models.Model):
    _inherit = "res.company"

    sale_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Operação Fiscal Padrão de Vendas",
    )

    copy_note = fields.Boolean(
        string="Copy Sale note on invoice",
        default=False,
    )

    delivery_costs = fields.Selection(
        selection=[("line", _("By Line")), ("total", _("By Total"))],
        string="Delivery costs should be define in Line or Total.",
        help="Define if costs of Insurance, Freight and Other Costs"
        " should be informed in Line or Total.",
        default="total",
    )
