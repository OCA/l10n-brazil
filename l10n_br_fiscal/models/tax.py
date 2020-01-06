# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp

from ..constants.fiscal import (FISCAL_IN, FISCAL_OUT, TAX_BASE_TYPE,
                                TAX_BASE_TYPE_PERCENT, TAX_DOMAIN)
from ..constants.icms import (ICMS_BASE_TYPE, ICMS_BASE_TYPE_DEFAULT,
                              ICMS_ST_BASE_TYPE, ICMS_ST_BASE_TYPE_DEFAULT)
from ..constants.pis_cofins import CST_COFINS_NO_TAXED, CST_PIS_NO_TAXED

TAX_DICT_VALUES = {
    "fiscal_tax_id": False,
    "tax_include": False,
    "tax_domain": False,
    "cst_id": False,
    "cst_code": False,
    "base_type": "percent",
    "base": 0.00,
    "percent_amount": 0.00,
    "percent_reduction": 0.00,
    "value_amount": 0.00,
    "uot_id": False,
    "tax_value": 0.00,
}


class Tax(models.Model):
    _name = "l10n_br_fiscal.tax"
    _order = "sequence, tax_domain, name"
    _description = "Tax"

    name = fields.Char(string="Name", size=256, required=True)

    sequence = fields.Integer(
        string="Sequence",
        default=10,
        related="tax_group_id.sequence",
        required=True,
        help="The sequence field is used to define "
        "order in which the tax lines are applied.",
    )

    tax_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="Tax Base Type",
        default=TAX_BASE_TYPE_PERCENT,
        required=True,
    )

    percent_amount = fields.Float(
        string="Percent",
        default="0.00",
        digits=dp.get_precision("Fiscal Tax Percent"),
        required=True,
    )

    percent_reduction = fields.Float(
        string="Percent Reduction",
        default="0.00",
        digits=dp.get_precision("Fiscal Tax Percent"),
        required=True,
    )

    percent_debit_credit = fields.Float(
        string="Percent Debit/Credit",
        default="0.00",
        digits=dp.get_precision("Fiscal Tax Percent"),
        required=True,
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        default=lambda self: self.env.ref("base.BRL"),
        string="Currency",
    )

    value_amount = fields.Float(
        string="Value",
        default="0.00",
        digits=dp.get_precision("Fiscal Tax Value"),
        required=True,
    )

    uot_id = fields.Many2one(comodel_name="uom.uom", string="Tax UoM")

    tax_group_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.group",
        string="Fiscal Tax Group",
        required=True,
    )

    tax_domain = fields.Selection(
        selection=TAX_DOMAIN,
        related="tax_group_id.tax_domain",
        string="Tax Domain",
        required=True,
        readonly=True,
    )

    cst_in_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST In",
        domain="[('cst_type', 'in', ('in', 'all')), "
        "('tax_domain', '=', tax_domain)]",
    )

    cst_out_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST Out",
        domain="[('cst_type', 'in', ('out', 'all')), "
        "('tax_domain', '=', tax_domain)]",
    )

    # ICMS Fields
    icms_base_type = fields.Selection(
        selection=ICMS_BASE_TYPE,
        string="ICMS Base Type",
        required=True,
        default=ICMS_BASE_TYPE_DEFAULT,
    )

    icms_st_base_type = fields.Selection(
        selection=ICMS_ST_BASE_TYPE,
        string=u"Tipo Base ICMS ST",
        required=True,
        default=ICMS_ST_BASE_TYPE_DEFAULT,
    )

    _sql_constraints = [
        ("fiscal_tax_code_uniq", "unique (name)", "Tax already exists with this name !")
    ]

    @api.multi
    def get_account_tax(self, operation_type=FISCAL_OUT):
        account_tax_type = {'out': 'sale', 'in': 'purchase'}
        type_tax_use = account_tax_type.get(operation_type, 'sale')

        account_taxes = self.env["account.tax"].search([
            ("fiscal_tax_id", "=", self.ids),
            ('active', '=', True),
            ('type_tax_use', '=', type_tax_use)])

        return account_taxes

    def cst_from_tax(self, operation_type=FISCAL_OUT):
        self.ensure_one()
        cst = self.env["l10n_br_fiscal.cst"]
        if operation_type == FISCAL_IN:
            cst = self.cst_in_id

        if operation_type == FISCAL_OUT:
            cst = self.cst_out_id
        return cst

    def _compute_icms(self, tax, tax_dict, **kwargs):
        return self._compute_generic(tax, tax_dict, **kwargs)

    def _compute_icmsn(self, tax, tax_dict, **kwargs):
        return self._compute_generic(tax, tax_dict, **kwargs)

    def _compute_ipi(self, tax, tax_dict, **kwargs):
        return self._compute_generic(tax, tax_dict, **kwargs)

    def _compute_icmsst(self, tax, tax_dict, **kwargs):
        return self._compute_generic(tax, tax_dict, **kwargs)

    def _compute_icms_difal(self, tax, tax_dict, **kwargs):
        return self._compute_generic(tax, tax_dict, **kwargs)

    def _compute_ii(self, tax, tax_dict, **kwargs):
        return self._compute_generic(tax, tax_dict, **kwargs)

    def _compute_pis(self, tax, tax_dict, **kwargs):
        cst = kwargs.get("cst", self.env["l10n_br_fiscal.cst"])
        if cst.code not in CST_PIS_NO_TAXED:
            tax_dict = self._compute_generic(tax, tax_dict, **kwargs)
        return tax_dict

    def _compute_cofins(self, tax, tax_dict, **kwargs):
        cst = kwargs.get("cst", self.env["l10n_br_fiscal.cst"])
        if cst.code not in CST_COFINS_NO_TAXED:
            tax_dict = self._compute_generic(tax, tax_dict, **kwargs)
        return tax_dict

    def _compute_generic(self, tax, tax_dict, **kwargs):
        company = kwargs.get("company", tax.env.user.company_id)
        currency = kwargs.get("currency", company.currency_id)
        precision = currency.decimal_places
        # price = kwargs.get('price', 0.00)
        # quantity = kwargs.get('quantity', 0.00)
        # uom_id = kwargs.get('uom_id')
        fiscal_price = kwargs.get("fiscal_price", 0.00)
        fiscal_quantity = kwargs.get("fiscal_quantity", 0.00)
        # uot_id = kwargs.get('uot_id')

        tax_dict["tax_include"] = tax.tax_group_id.tax_include
        tax_dict["fiscal_tax_id"] = tax.id
        tax_dict["tax_domain"] = tax.tax_domain

        if tax.tax_base_type == "percent":
            tax_dict["base_type"] = tax.tax_base_type
            tax_dict["percent_amount"] = tax.percent_amount
            tax_dict["percent_reduction"] = tax.percent_reduction

            # Compute Tax Base
            base = round(fiscal_price * fiscal_quantity, precision)

            # Compute Tax Base Reduction
            base_reduction = round(base * abs(tax.percent_reduction / 100), precision)

            # Compute Tax Base Amount
            base_amount = base - base_reduction

            tax_dict["base"] = base_amount

            # Compute Tax Value
            tax_value = round(base_amount * (tax.percent_amount / 100), precision)

            tax_dict["tax_value"] = tax_value

        if tax.tax_base_type == "quantity":
            # Tax base
            base_amount = fiscal_quantity
            tax_dict["base"] = base_amount

            # Tax value by unit
            tax_dict["value_amount"] = tax.value_amount

            tax_dict["tax_value"] = round(base_amount * tax.value_amount, precision)

        if tax.tax_base_type == "fixed":
            # Compute Tax Base
            base = round(fiscal_price * fiscal_quantity, precision)

            # Compute Tax Base Reduction
            base_reduction = round(base * abs(tax.percent_reduction / 100), precision)

            # Compute Tax Base Amount
            base_amount = base_amount - base_reduction

            tax_dict["base"] = base_amount
            tax_dict["value_amount"] = tax.value_amount

        return tax_dict

    @api.multi
    def compute_taxes(self, **kwargs):
        """
        arguments:
            company,
            partner,
            product,
            fiscal_price,
            fiscal_quantity,
            ncm,
            cest,
            operation_type,
        """
        taxes = {}
        for tax in self:
            tax_dict = TAX_DICT_VALUES.copy()
            taxes[tax.tax_domain] = tax_dict
            try:
                # Define CST FROM TAX
                operation_type = kwargs.get("operation_type", FISCAL_OUT)
                kwargs.update({"cst": tax.cst_from_tax(operation_type)})

                compute_method = getattr(self, "_compute_%s" % tax.tax_domain)
                taxes[tax.tax_domain].update(
                    compute_method(tax, taxes[tax.tax_domain], **kwargs)
                )
            except AttributeError:
                taxes[tax.tax_domain].update(
                    tax._compute_generic(tax, taxes[tax.tax_domain], **kwargs)
                )
                # Caso não exista campos especificos dos impostos
                # no documento fiscal, os mesmos são calculados.
                continue
        return taxes
