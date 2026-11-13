# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class OperationLine(models.Model):
    _inherit = "l10n_br_fiscal.operation.line"

    fiscal_position_id = fields.Many2one(
        comodel_name="account.fiscal.position",
        string="Fiscal Position",
        company_dependent=True,
    )

    icms_no_credit = fields.Boolean(
        string="ICMS without Credit",
        help="Purchases under this line do not take the ICMS credit, as with "
        "material for use and consumption (LC 87/1996, art. 33, I): the vendor "
        "bill books no ICMS to recover and the ICMS stays in the cost of the line.",
    )
