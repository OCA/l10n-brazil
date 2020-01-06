# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.addons.l10n_br_fiscal.constants.fiscal import TAX_DOMAIN


class AccountTaxAbstract(models.AbstractModel):
    _name = "account.tax.fiscal.abstract"
    _description = "Account Tax Fiscal Abstract"

    fiscal_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax", string="Fiscal Tax"
    )

    fiscal_cst_in_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        related="fiscal_tax_id.cst_in_id",
        string="CST Input",
    )

    fiscal_cst_out_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        related="fiscal_tax_id.cst_out_id",
        string="CST Output",
    )

    fiscal_tax_domain = fields.Selection(
        selection=TAX_DOMAIN, related="fiscal_tax_id.tax_domain", string="Tax Domain"
    )

    @api.onchange("fiscal_tax_id")
    def _onchange_fiscal_tax_id(self):
        if self.fiscal_tax_id:
            fiscal_tax = self.fiscal_tax_id
            fiscal_type = {"sale": _("Out"), "purchase": _("In")}

            if fiscal_tax.tax_base_type == 'percent':
                type_amount = 'percent'
                tax_amount = fiscal_tax.percent_amount
            else:
                type_amount = 'fixed'
                tax_amount = fiscal_tax.value_amount

            self.amount_type = type_amount
            self.amount = tax_amount
            self.description = fiscal_tax.name

            colect_account_id = fiscal_tax.tax_group_id.colect_account_id.id
            recover_account_id = fiscal_tax.tax_group_id.recover_account_id.id

            if self.type_tax_use == 'purchase':
                self.account_id = recover_account_id
                self.refund_account_id = colect_account_id
            else:
                self.account_id = colect_account_id
                self.refund_account_id = recover_account_id

            self.name = "{} {}".format(
                self.fiscal_tax_id.name, fiscal_type.get(self.type_tax_use, "")
            )
