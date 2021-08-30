from odoo import fields, models


class AccountTaxGroupAccountTemplate(models.Model):
    _name = "l10n_br_coa.account.tax.group.account.template"
    _description = "Account Tax Group Account Template"

    chart_template_id = fields.Many2one(
        comodel_name="account.chart.template", string="Chart Template", required=True
    )

    tax_group_id = fields.Many2one(
        comodel_name="account.tax.group", string="Tax Group", required=True
    )

    account_id = fields.Many2one(
        comodel_name="account.account.template",
        string="Tax Account",
    )

    refund_account_id = fields.Many2one(
        comodel_name="account.account.template",
        string="Tax Account on Credit Notes",
    )

    ded_account_id = fields.Many2one(
        comodel_name="account.account.template",
        string="Deductible Tax Account",
    )

    ded_refund_account_id = fields.Many2one(
        comodel_name="account.account.template",
        string="Deductible Tax Account on Credit Notes",
    )
