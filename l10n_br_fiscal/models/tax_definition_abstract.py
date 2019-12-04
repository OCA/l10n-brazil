# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models

from ..constants.fiscal import FISCAL_IN_OUT, FISCAL_OUT, TAX_DOMAIN


class TaxDefinitionAbstract(models.AbstractModel):
    _name = "l10n_br_fiscal.tax.definition.abstract"
    _description = "Tax Definition Abstract"

    type_in_out = fields.Selection(
        selection=FISCAL_IN_OUT, string="Type", required=True, default=FISCAL_OUT
    )

    tax_group_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.group", string="Tax Group"
    )

    custom_tax = fields.Boolean(string="Custom Tax")

    tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        domain="[('tax_group_id', '=', tax_group_id)]",
        string="Tax",
    )

    cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        domain="[('cst_type', 'in', (type_in_out, 'all')),"
        "('tax_domain', '=', tax_domain)]",
        string="CST",
    )

    cst_code = fields.Char(string="CST Code", related="cst_id.code")

    tax_domain = fields.Selection(
        selection=TAX_DOMAIN,
        related="tax_group_id.tax_domain",
        store=True,
        string="Tax Domain",
    )

    is_taxed = fields.Boolean(string="Taxed?")

    is_debit_credit = fields.Boolean(string="Debit/Credit?")

    tax_retention = fields.Boolean(string="Tax Retention?")

    @api.onchange("is_taxed")
    def _onchange_tribute(self):
        if not self.is_taxed:
            self.is_debit_credit = False
        else:
            self.is_debit_credit = True

    @api.onchange("custom_tax")
    def _onchange_custom_tax(self):
        if not self.custom_tax:
            self.tax_id = False
            self.cst_id = False

    @api.onchange("tax_id")
    def _onchange_tax_id(self):
        if self.tax_id:
            if self.type_in_out == FISCAL_OUT:
                self.cst_id = self.tax_id.cst_out_id
            else:
                self.cst_id = self.tax_id.cst_in_id
