# Copyright (C) 2020 - TODAY Renato Lima - Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountTaxGroup(models.Model):
    _inherit = "account.tax.group"

    account_id = fields.Many2one(
        comodel_name="account.account.template",
        string="Tax Account",
        company_dependent=True,
    )

    refund_account_id = fields.Many2one(
        comodel_name="account.account.template",
        string="Tax Account on Credit Notes",
        company_dependent=True,
    )

    ded_account_id = fields.Many2one(
        comodel_name="account.account.template",
        string="Deductible Tax Account",
        company_dependent=True,
    )

    ded_refund_account_id = fields.Many2one(
        comodel_name="account.account.template",
        string="Deductible Tax Account on Credit Notes",
        company_dependent=True,
    )
