# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models

# from odoo.addons.account.models.account_invoice import TYPE2JOURNAL

FISCAL_TYPE_INVOICE = {
    "purchase": "in_invoice",
    "purchase_refund": "in_refund",
    "return_in": "in_refund",
    "sale": "out_invoice",
    "sale_refund": "out_refund",
    "return_out": "out_refund",
    "other": "out_invoice",
}


class Operation(models.Model):
    _inherit = "l10n_br_fiscal.operation"

    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Account Journal",
        company_dependent=True,
        domain="[('type', 'in', {'out': ['sale', 'general'], 'in': "
        "['purchase', 'general'], 'all': ['sale', 'purchase', "
        "'general']}.get(fiscal_operation_type, []))]",
    )

    fiscal_position_id = fields.Many2one(
        comodel_name="account.fiscal.position",
        string="Fiscal Position",
        company_dependent=True,
    )

    deductible_taxes = fields.Boolean(
        company_dependent=True,
    )

    def _line_domain(self, company, partner, product):
        domain = super()._line_domain(company=company, partner=partner, product=product)

        domain += [
            "|",
            ("fiscal_position_id", "=", partner.property_account_position_id.id),
            ("fiscal_position_id", "=", False),
        ]

        return domain
