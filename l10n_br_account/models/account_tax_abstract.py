# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.addons.l10n_br_fiscal.constants.fiscal import TAX_DOMAIN


class AccountTaxAbstract(models.AbstractModel):
    _name = "account.tax.fiscal.abstract"
    _description = "Account Tax Fiscal Abstract"

    @api.onchange("fiscal_tax_id")
    def _onchange_fiscal_tax_ids(self):
        if self.fiscal_tax_ids:
            fiscal_tax = self.fiscal_tax_ids[0]
            fiscal_type = {"sale": _("Out"), "purchase": _("In")}

            self.amount_type = type_amount
            self.amount = tax_amount
            self.description = fiscal_tax.tax_group_id.name

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
