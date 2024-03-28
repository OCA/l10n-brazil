# Copyright (C) 2023 - Diego Paradeda - KMEE

from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def _get_default_tax_account(self, repartition_line):
        """This is required to remap the tax line onto the same account as
        the origin line, e.g. ICMS -> Estoque."""
        account = super()._get_default_tax_account(repartition_line)

        if (
            self.fiscal_operation_line_id
            and repartition_line.tax_id.tax_group_id.fiscal_tax_group_id
            in self.fiscal_operation_line_id.non_creditable_tax_definition_ids
        ):
            account = self.account_id

        return account
