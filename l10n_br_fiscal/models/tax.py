# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.tools import float_is_zero

from ..constants.fiscal import (
    FINAL_CUSTOMER_YES,
    FISCAL_IN,
    FISCAL_OUT,
    NFE_IND_IE_DEST_1,
    NFE_IND_IE_DEST_2,
    NFE_IND_IE_DEST_9,
    TAX_BASE_TYPE,
    TAX_BASE_TYPE_PERCENT,
    TAX_BASE_TYPE_VALUE,
)
from ..constants.icms import (
    ICMS_BASE_TYPE,
    ICMS_BASE_TYPE_DEFAULT,
    ICMS_DIFAL_DOUBLE_BASE,
    ICMS_DIFAL_PARTITION,
    ICMS_DIFAL_UNIQUE_BASE,
    ICMS_ORIGIN_TAX_IMPORTED,
    ICMS_SN_CST_WITH_CREDIT,
    ICMS_ST_BASE_TYPE,
    ICMS_ST_BASE_TYPE_DEFAULT,
    ICSM_CST_CSOSN_ST_BASE,
)

TAX_DICT_VALUES = {
    "name": False,
    "fiscal_tax_id": False,
    "tax_include": False,
    "tax_withholding": False,
    "tax_domain": False,
    "cst_id": False,
    "cst_code": False,
    "base_type": "percent",
    "base": 0.00,
    "base_reduction": 0.00,
    "percent_amount": 0.00,
    "percent_reduction": 0.00,
    "value_amount": 0.00,
    "uot_id": False,
    "tax_value": 0.00,
    "compute_reduction": True,
}


class Tax(models.Model):
    _name = "l10n_br_fiscal.tax"
    _order = "sequence, tax_domain, name"
    _description = "Fiscal Tax"

    name = fields.Char(string="Name", size=256, required=True)

    sequence = fields.Integer(
        string="Sequence",
        related="tax_group_id.sequence",
        help="The sequence field is used to define the "
        "order in which taxes are displayed.",
        store=True,
    )

    compute_sequence = fields.Integer(
        string="Compute Sequence",
        related="tax_group_id.compute_sequence",
        help="The sequence field is used to define "
        "order in which the tax lines are applied.",
    )

    tax_scope = fields.Selection(
        related="tax_group_id.tax_scope",
        store=True,
    )

    tax_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="Tax Base Type",
        default=TAX_BASE_TYPE_PERCENT,
        required=True,
    )

    percent_amount = fields.Float(
        string="Percent", digits="Fiscal Tax Percent", required=True
    )

    percent_reduction = fields.Float(
        string="Percent Reduction",
        digits="Fiscal Tax Percent",
        required=True,
    )

    percent_debit_credit = fields.Float(
        string="Percent Debit/Credit",
        digits="Fiscal Tax Percent",
        required=True,
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        default=lambda self: self.env.ref("base.BRL"),
        string="Currency",
    )

    value_amount = fields.Float(
        string="Value", digits="Fiscal Tax Value", required=True
    )

    uot_id = fields.Many2one(comodel_name="uom.uom", string="Tax UoM")

    tax_group_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.group",
        string="Fiscal Tax Group",
        required=True,
    )

    tax_domain = fields.Selection(
        related="tax_group_id.tax_domain",
        string="Tax Domain",
        readonly=True,
        store=True,
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

    icmsst_base_type = fields.Selection(
        selection=ICMS_ST_BASE_TYPE,
        string="ICMS ST Base Type",
        required=True,
        default=ICMS_ST_BASE_TYPE_DEFAULT,
    )

    icmsst_mva_percent = fields.Float(
        string="MVA Percent",
        digits="Fiscal Tax Percent",
        required=True,
    )

    icmsst_value = fields.Float(
        string="PFC Value", digits="Fiscal Tax Value", required=True
    )

    _sql_constraints = [
        ("fiscal_tax_code_uniq", "unique (name)", "Tax already exists with this name !")
    ]

    def cst_from_tax(self, fiscal_operation_type=FISCAL_OUT):
        self.ensure_one()
        cst = self.env["l10n_br_fiscal.cst"]
        if fiscal_operation_type == FISCAL_IN:
            cst = self.cst_in_id

        if fiscal_operation_type == FISCAL_OUT:
            cst = self.cst_out_id
        return cst

    def _compute_tax_base(self, tax, tax_dict, **kwargs):
        company = kwargs.get("company", tax.env.company)
        currency = kwargs.get("currency", company.currency_id)
        precision = currency.decimal_places
        fiscal_price = kwargs.get("fiscal_price", 0.00)
        fiscal_quantity = kwargs.get("fiscal_quantity", 0.00)
        add_to_base = kwargs.get("add_to_base", 0.00)
        remove_from_base = kwargs.get("remove_from_base", 0.00)
        compute_reduction = kwargs.get("compute_reduction", True)

        base = 0.00

        if not tax_dict.get("percent_amount") and tax.percent_amount:
            tax_dict["percent_amount"] = tax.percent_amount
            tax_dict["value_amount"] = tax.value_amount

        if tax_dict["base_type"] == "percent":
            # Compute initial Tax Base for base_type Percent
            base = round(fiscal_price * fiscal_quantity, precision)

        if tax_dict["base_type"] == "quantity":
            # Compute initial Tax Base for base_type Quantity
            base = fiscal_quantity

        if tax_dict["base_type"] == "fixed":
            # Compute initial Tax Base
            base = round(fiscal_price * fiscal_quantity, precision)

        # Update Base Value
        base_amount = (base + add_to_base) - remove_from_base

        # Compute Tax Base Reduction
        base_reduction = round(
            base_amount * abs(tax.percent_reduction / 100), precision
        )

        # Compute Tax Base Amount
        if compute_reduction:
            base_amount -= base_reduction

        if tax_dict.get("icmsst_mva_percent"):
            base_amount *= 1 + (tax_dict["icmsst_mva_percent"] / 100)

        if (
            not tax.percent_amount
            and not tax.value_amount
            and not tax_dict.get("percent_amount")
            and not tax_dict.get("value_amount")
        ):
            tax_dict["base"] = 0.00
        else:
            tax_dict["base"] = base_amount

        return tax_dict

    def _compute_tax(self, tax, taxes_dict, **kwargs):

        tax_dict = taxes_dict.get(tax.tax_domain)
        tax_dict["name"] = tax.name
        tax_dict["base_type"] = tax.tax_base_type
        tax_dict["tax_include"] = tax.tax_group_id.tax_include
        tax_dict["tax_withholding"] = tax.tax_group_id.tax_withholding
        tax_dict["fiscal_tax_id"] = tax.id
        tax_dict["tax_domain"] = tax.tax_domain
        tax_dict["percent_reduction"] = tax.percent_reduction
        tax_dict["percent_amount"] = tax_dict.get("percent_amount", tax.percent_amount)

        company = kwargs.get("company", tax.env.company)
        # partner = kwargs.get("partner")
        currency = kwargs.get("currency", company.currency_id)
        precision = currency.decimal_places
        # product = kwargs.get("product")
        # price_unit = kwargs.get("price_unit", 0.00)
        # quantity = kwargs.get("quantity", 0.00)
        # uom_id = kwargs.get("uom_id")
        # fiscal_price = kwargs.get("fiscal_price", 0.00)
        # fiscal_quantity = kwargs.get("fiscal_quantity", 0.00)
        # uot_id = kwargs.get("uot_id")
        discount_value = kwargs.get("discount_value", 0.00)
        # insurance_value = kwargs.get("insurance_value", 0.00)
        # other_value = kwargs.get("other_value", 0.00)
        # freight_value = kwargs.get("freight_value", 0.00)
        # ncm = kwargs.get("ncm")
        # cest = kwargs.get("cest")
        operation_line = kwargs.get("operation_line")
        remove_from_base = [discount_value]

        if tax.tax_group_id.base_without_icms:
            # Get Computed ICMS Tax
            tax_dict_icms = taxes_dict.get("icms", {})
            remove_from_base.append(tax_dict_icms.get("tax_value", 0.00))

        kwargs.update(
            {
                "remove_from_base": sum(remove_from_base),
            }
        )

        # TODO futuramente levar em consideração outros tipos de base de calculo
        if float_is_zero(tax_dict.get("base", 0.00), precision):
            tax_dict = self._compute_tax_base(tax, tax_dict, **kwargs)

        fiscal_operation_type = operation_line.fiscal_operation_type or FISCAL_OUT
        tax_dict["cst_id"] = tax.cst_from_tax(fiscal_operation_type)

        base_amount = tax_dict.get("base", 0.00)

        if tax_dict["base_type"] == "percent":
            # Compute Tax Value
            tax_value = round(
                base_amount * (tax_dict["percent_amount"] / 100), precision
            )

            tax_dict["tax_value"] = tax_value

        if tax_dict["base_type"] in ("quantity", "fixed"):

            tax_dict["tax_value"] = round(
                base_amount * tax_dict["value_amount"], precision
            )

        return tax_dict

    def _compute_estimate_taxes(self, **kwargs):
        company = kwargs.get("company")
        product = kwargs.get("product")
        fiscal_price = kwargs.get("fiscal_price")
        fiscal_quantity = kwargs.get("fiscal_quantity")
        currency = kwargs.get("currency", company.currency_id)
        precision = currency.decimal_places
        ncm = kwargs.get("ncm") or product.ncm_id
        nbs = kwargs.get("nbs") or product.nbs_id
        icms_origin = kwargs.get("icms_origin") or product.icms_origin
        op_line = kwargs.get("operation_line")
        amount_estimate_tax = 0.00
        amount_total = round(fiscal_price * fiscal_quantity, precision)

        if op_line and (
            op_line.fiscal_operation_type == FISCAL_OUT
            and op_line.fiscal_operation_id.fiscal_type == "sale"
        ):
            if nbs:
                amount_estimate_tax = round(
                    amount_total * (nbs.estimate_tax_national / 100), precision
                )
            elif ncm:
                if icms_origin in ICMS_ORIGIN_TAX_IMPORTED:
                    amount_estimate_tax = round(
                        amount_total * (ncm.estimate_tax_imported / 100), precision
                    )
                else:
                    amount_estimate_tax = round(
                        amount_total * (ncm.estimate_tax_national / 100), precision
                    )

        return amount_estimate_tax

    def _compute_icms(self, tax, taxes_dict, **kwargs):
        partner = kwargs.get("partner")
        company = kwargs.get("company")
        product = kwargs.get("product")
        currency = kwargs.get("currency", company.currency_id)
        precision = currency.decimal_places
        ncm = kwargs.get("ncm")
        nbm = kwargs.get("nbm")
        cest = kwargs.get("cest")
        operation_line = kwargs.get("operation_line")
        discount_value = kwargs.get("discount_value", 0.00)
        insurance_value = kwargs.get("insurance_value", 0.00)
        freight_value = kwargs.get("freight_value", 0.00)
        other_value = kwargs.get("other_value", 0.00)

        add_to_base = [insurance_value, freight_value, other_value]
        remove_from_base = [discount_value]

        # Get Computed IPI Tax
        tax_dict_ipi = taxes_dict.get("ipi", {})

        if partner.ind_ie_dest in (NFE_IND_IE_DEST_2, NFE_IND_IE_DEST_9) or (
            operation_line.fiscal_operation_id.ind_final == FINAL_CUSTOMER_YES
        ):
            # Add IPI in ICMS Base
            add_to_base.append(tax_dict_ipi.get("tax_value", 0.00))

        kwargs.update(
            {
                "add_to_base": sum(add_to_base),
                "remove_from_base": sum(remove_from_base),
                "icms_base_type": tax.icms_base_type,
            }
        )

        taxes_dict[tax.tax_domain].update(
            self._compute_tax_base(tax, taxes_dict.get(tax.tax_domain), **kwargs)
        )

        taxes_dict[tax.tax_domain].update(self._compute_tax(tax, taxes_dict, **kwargs))

        taxes_dict[tax.tax_domain].update({"icms_base_type": tax.icms_base_type})

        # DIFAL
        # TODO
        # and operation_line.ind_final == FINAL_CUSTOMER_YES):
        if (
            company.state_id != partner.state_id
            and operation_line.fiscal_operation_type == FISCAL_OUT
            and partner.ind_ie_dest == NFE_IND_IE_DEST_9
            and taxes_dict[tax.tax_domain].get("tax_value")
        ):
            tax_icms_difal = company.icms_regulation_id.map_tax_icms_difal(
                company, partner, product, ncm, nbm, cest, operation_line
            )
            tax_icmsfcp_difal = company.icms_regulation_id.map_tax_icmsfcp(
                company, partner, product, ncm, nbm, cest, operation_line
            )

            # Difal - Origin Percent
            icms_origin_perc = taxes_dict[tax.tax_domain].get("percent_amount")

            # Difal - Origin Value
            icms_origin_value = taxes_dict[tax.tax_domain].get("tax_value")

            # Difal - Destination Percent
            icms_dest_perc = 0.00
            if tax_icms_difal:
                icms_dest_perc = tax_icms_difal[0].percent_amount

            # Difal - FCP Percent
            icmsfcp_perc = 0.00
            if tax_icmsfcp_difal:
                icmsfcp_perc = tax_icmsfcp_difal[0].percent_amount

            # Difal - Base
            icms_base = taxes_dict[tax.tax_domain].get("base")
            difal_icms_base = 0.00

            # Difal - ICMS Dest Value
            icms_dest_value = round(icms_base * (icms_dest_perc / 100), precision)

            if partner.state_id.code in ICMS_DIFAL_UNIQUE_BASE:
                difal_icms_base = icms_base

            if partner.state_id.code in ICMS_DIFAL_DOUBLE_BASE:
                difal_icms_base = round(
                    (icms_base - icms_origin_value)
                    / (1 - ((icms_dest_perc + icmsfcp_perc) / 100)),
                    precision,
                )

                icms_dest_value = round(
                    difal_icms_base * (icms_dest_perc / 100), precision
                )

            difal_value = icms_dest_value - icms_origin_value

            # Difal - Sharing Percent
            date_year = fields.Date.today().year

            if date_year >= 2019:
                taxes_dict[tax.tax_domain].update(ICMS_DIFAL_PARTITION[2019])
            else:
                if date_year == 2018:
                    taxes_dict[tax.tax_domain].update(ICMS_DIFAL_PARTITION[2018])
                if date_year == 2017:
                    taxes_dict[tax.tax_domain].update(ICMS_DIFAL_PARTITION[2017])
                else:
                    taxes_dict[tax.tax_domain].update(ICMS_DIFAL_PARTITION[2016])

            difal_share_origin = taxes_dict[tax.tax_domain].get("difal_origin_perc")

            difal_share_dest = taxes_dict[tax.tax_domain].get("difal_dest_perc")

            difal_origin_value = round(
                difal_value * difal_share_origin / 100, precision
            )
            difal_dest_value = round(difal_value * difal_share_dest / 100, precision)

            taxes_dict[tax.tax_domain].update(
                {
                    "icms_origin_perc": icms_origin_perc,
                    "icms_dest_perc": icms_dest_perc,
                    "icms_dest_base": difal_icms_base,
                    "icms_sharing_percent": difal_share_dest,
                    "icms_origin_value": difal_origin_value,
                    "icms_dest_value": difal_dest_value,
                }
            )

        return taxes_dict

    def _compute_icmsfcp(self, tax, taxes_dict, **kwargs):
        """Compute ICMS FCP"""
        partner = kwargs.get("partner")
        company = kwargs.get("company")
        icms_cst_id = kwargs.get("icms_cst_id")

        if taxes_dict.get("icms"):
            if company.state_id != partner.state_id:
                taxes_dict[tax.tax_domain]["base"] = taxes_dict["icms"].get(
                    "icms_dest_base", 0.0
                )
            else:
                taxes_dict[tax.tax_domain]["base"] = taxes_dict["icms"].get("base", 0.0)
        elif taxes_dict.get("icmssn"):
            taxes_dict[tax.tax_domain]["base"] = taxes_dict["icmssn"].get("base", 0.0)

        taxes_dict[tax.tax_domain].pop("percent_amount", None)

        taxes_dict[tax.tax_domain].update(self._compute_tax(tax, taxes_dict, **kwargs))

        taxes_dict[tax.tax_domain].update({"icms_base_type": tax.icms_base_type})

        taxes_dict[tax.tax_domain]["fcpst_base"] = taxes_dict.get("icmsst", {}).get(
            "base", 0.00
        )

        # TODO Improve this condition
        if icms_cst_id.code in ICSM_CST_CSOSN_ST_BASE:
            taxes_dict[tax.tax_domain]["fcpst_value"] = taxes_dict[tax.tax_domain][
                "fcpst_base"
            ] * (taxes_dict[tax.tax_domain]["percent_amount"] / 100)
            taxes_dict[tax.tax_domain]["fcpst_value"] -= taxes_dict[tax.tax_domain][
                "tax_value"
            ]

        return self._compute_tax(tax, taxes_dict, **kwargs)

    def _compute_icmsst(self, tax, taxes_dict, **kwargs):
        # partner = kwargs.get("partner")
        # company = kwargs.get("company")
        discount_value = kwargs.get("discount_value", 0.00)
        insurance_value = kwargs.get("insurance_value", 0.00)
        freight_value = kwargs.get("freight_value", 0.00)
        other_value = kwargs.get("other_value", 0.00)

        add_to_base = [insurance_value, freight_value, other_value]
        remove_from_base = [discount_value]

        # Get Computed IPI Tax
        tax_dict_ipi = taxes_dict.get("ipi", {})
        add_to_base.append(tax_dict_ipi.get("tax_value", 0.00))

        kwargs.update(
            {
                "add_to_base": sum(add_to_base),
                "remove_from_base": sum(remove_from_base),
                "icmsst_base_type": tax.icmsst_base_type,
            }
        )
        if taxes_dict.get(tax.tax_domain):
            taxes_dict[tax.tax_domain]["icmsst_mva_percent"] = tax.icmsst_mva_percent

        taxes_dict[tax.tax_domain].update(
            self._compute_tax_base(tax, taxes_dict.get(tax.tax_domain), **kwargs)
        )

        tax_dict = self._compute_tax(tax, taxes_dict, **kwargs)
        if tax_dict.get("icmsst_mva_percent"):
            tax_dict["tax_value"] -= taxes_dict.get("icms", {}).get("tax_value", 0.0)

        return tax_dict

    def _compute_icmssn(self, tax, taxes_dict, **kwargs):
        tax_dict = taxes_dict.get(tax.tax_domain)
        partner = kwargs.get("partner")
        company = kwargs.get("company")
        cst = kwargs.get("cst", self.env["l10n_br_fiscal.cst"])
        discount_value = kwargs.get("discount_value", 0.00)
        insurance_value = kwargs.get("insurance_value", 0.00)
        freight_value = kwargs.get("freight_value", 0.00)
        other_value = kwargs.get("other_value", 0.00)
        icmssn_range = kwargs.get("icmssn_range")

        add_to_base = [insurance_value, freight_value, other_value]
        remove_from_base = [discount_value]

        # Get Computed IPI Tax
        tax_dict_ipi = taxes_dict.get("ipi", {})

        # Partner not ICMS's Contributor
        if partner.ind_ie_dest == NFE_IND_IE_DEST_9:
            # Add IPI in ICMS Base
            add_to_base.append(tax_dict_ipi.get("tax_value", 0.00))

        # Partner ICMS's Contributor
        if partner.ind_ie_dest in (NFE_IND_IE_DEST_1, NFE_IND_IE_DEST_2):
            if cst.code in ICMS_SN_CST_WITH_CREDIT:
                icms_sn_percent = round(
                    company.simplifed_tax_percent
                    * (icmssn_range.tax_icms_percent / 100),
                    2,
                )

                tax_dict["percent_amount"] = icms_sn_percent
                tax_dict["value_amount"] = icms_sn_percent

        kwargs.update(
            {
                "add_to_base": sum(add_to_base),
                "remove_from_base": sum(remove_from_base),
            }
        )

        taxes_dict.update(
            self._compute_tax_base(tax, taxes_dict.get(tax.tax_domain), **kwargs)
        )

        return self._compute_tax(tax, taxes_dict, **kwargs)

    def _compute_issqn(self, tax, taxes_dict, **kwargs):
        return self._compute_generic(tax, taxes_dict, **kwargs)

    def _compute_issqn_wh(self, tax, taxes_dict, **kwargs):
        return self._compute_generic(tax, taxes_dict, **kwargs)

    def _compute_csll(self, tax, taxes_dict, **kwargs):
        return self._compute_generic(tax, taxes_dict, **kwargs)

    def _compute_csll_wh(self, tax, taxes_dict, **kwargs):
        return self._compute_generic(tax, taxes_dict, **kwargs)

    def _compute_irpj(self, tax, taxes_dict, **kwargs):
        return self._compute_generic(tax, taxes_dict, **kwargs)

    def _compute_irpj_wh(self, tax, taxes_dict, **kwargs):
        return self._compute_generic(tax, taxes_dict, **kwargs)

    def _compute_inss(self, tax, taxes_dict, **kwargs):
        return self._compute_generic(tax, taxes_dict, **kwargs)

    def _compute_inss_wh(self, tax, taxes_dict, **kwargs):
        return self._compute_generic(tax, taxes_dict, **kwargs)

    def _compute_ipi(self, tax, taxes_dict, **kwargs):
        discount_value = kwargs.get("discount_value", 0.00)
        insurance_value = kwargs.get("insurance_value", 0.00)
        freight_value = kwargs.get("freight_value", 0.00)
        other_value = kwargs.get("other_value", 0.00)

        add_to_base = [insurance_value, freight_value, other_value]
        remove_from_base = [discount_value]

        kwargs.update(
            {
                "add_to_base": sum(add_to_base),
                "remove_from_base": sum(remove_from_base),
            }
        )

        taxes_dict[tax.tax_domain].update(
            self._compute_tax_base(tax, taxes_dict.get(tax.tax_domain), **kwargs)
        )

        return self._compute_generic(tax, taxes_dict, **kwargs)

    def _compute_ii(self, tax, taxes_dict, **kwargs):
        return self._compute_generic(tax, taxes_dict, **kwargs)

    def _compute_pis(self, tax, taxes_dict, **kwargs):
        return self._compute_generic(tax, taxes_dict, **kwargs)

    def _compute_pis_wh(self, tax, taxes_dict, **kwargs):
        return self._compute_generic(tax, taxes_dict, **kwargs)

    def _compute_cofins(self, tax, taxes_dict, **kwargs):
        return self._compute_generic(tax, taxes_dict, **kwargs)

    def _compute_cofins_wh(self, tax, taxes_dict, **kwargs):
        return self._compute_generic(tax, taxes_dict, **kwargs)

    def _compute_generic(self, tax, taxes_dict, **kwargs):
        taxes_dict[tax.tax_domain].update(
            self._compute_tax_base(tax, taxes_dict.get(tax.tax_domain), **kwargs)
        )

        return self._compute_tax(tax, taxes_dict, **kwargs)

    def compute_taxes(self, **kwargs):
        """
        arguments:
            company,
            partner,
            product,
            price_unit,
            quantity,
            uom_id,
            fiscal_price,
            fiscal_quantity,
            uot_id,
            discount_value,
            insurance_value,
            other_value,
            freight_value,
            ncm,
            nbs,
            nbm,
            cest,
            operation_line,
            icmssn_range,
            icms_origin,
        return
            {
                'amount_included': float
                'amount_not_included': float
                'amount_withholding': float
                'taxes': dict
            }
        """
        result_amounts = {
            "amount_included": 0.00,
            "amount_not_included": 0.00,
            "amount_withholding": 0.00,
            "estimate_tax": 0.00,
            "taxes": {},
        }
        taxes = {}

        for tax in self.sorted(key=lambda t: t.compute_sequence):
            taxes[tax.tax_domain] = dict(TAX_DICT_VALUES)
            try:
                # Define CST FROM TAX
                operation_line = kwargs.get("operation_line")
                fiscal_operation_type = (
                    operation_line.fiscal_operation_type or FISCAL_OUT
                )
                kwargs.update({"cst": tax.cst_from_tax(fiscal_operation_type)})

                compute_method = getattr(self, "_compute_%s" % tax.tax_domain)
                taxes[tax.tax_domain].update(compute_method(tax, taxes, **kwargs))
                if taxes[tax.tax_domain]["tax_include"]:
                    result_amounts["amount_included"] += taxes[tax.tax_domain].get(
                        "tax_value", 0.00
                    )
                else:
                    result_amounts["amount_not_included"] += taxes[tax.tax_domain].get(
                        "tax_value", 0.00
                    )

                if taxes[tax.tax_domain]["tax_withholding"]:
                    result_amounts["amount_withholding"] += taxes[tax.tax_domain].get(
                        "tax_value", 0.00
                    )

            except AttributeError:
                taxes[tax.tax_domain].update(tax._compute_generic(tax, taxes, **kwargs))
                # Caso não exista campos especificos dos impostos
                # no documento fiscal, os mesmos são calculados.
                continue

        # Estimate taxes
        result_amounts["estimate_tax"] = self._compute_estimate_taxes(**kwargs)
        result_amounts["taxes"] = taxes
        return result_amounts

    @api.onchange("icmsst_base_type")
    def _onchange_icmsst_base_type(self):
        if self.icmsst_base_type:
            ICMS_ST_BASE_TYPE_REL = {
                "0": TAX_BASE_TYPE_VALUE,
                "1": TAX_BASE_TYPE_VALUE,
                "2": TAX_BASE_TYPE_VALUE,
                "3": TAX_BASE_TYPE_VALUE,
                "4": TAX_BASE_TYPE_PERCENT,
                "5": TAX_BASE_TYPE_VALUE,
            }

            self.tax_base_type = ICMS_ST_BASE_TYPE_REL.get(self.icmsst_base_type)
