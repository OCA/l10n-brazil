# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.tools.misc import formatLang

from odoo.addons.l10n_br_fiscal.constants.fiscal import FINAL_CUSTOMER_NO


class AccountTax(models.Model):
    _inherit = "account.tax"

    fiscal_tax_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.tax",
        related="tax_group_id.fiscal_tax_group_id.tax_ids",
        string="Fiscal Taxes",
    )

    def compute_all(
        self,
        price_unit,
        currency=None,
        quantity=1.0,
        product=None,
        partner=None,
        is_refund=False,
        handle_price_include=True,
        include_caba_tags=False,
        rounding_method=None,
        fixed_multiplicator=1,
        fiscal_taxes=None,
        operation_line=False,
        ncm=None,
        nbs=None,
        nbm=None,
        cest=None,
        cfop=None,
        discount_value=None,
        insurance_value=None,
        other_value=None,
        ii_customhouse_charges=None,
        freight_value=None,
        fiscal_price=None,
        fiscal_quantity=None,
        uot_id=None,
        icmssn_range=None,
        icms_origin=None,
        ind_final=FINAL_CUSTOMER_NO,
    ):
        """Returns all information required to apply taxes
            (in self + their children in case of a tax goup).
            We consider the sequence of the parent for group of taxes.
                Eg. considering letters as taxes and alphabetic order
                as sequence :
                [G, B([A, D, F]), E, C] will be computed as [A, D, F, C, E, G]
        RETURN: {
            'total_excluded': 0.0,    # Total without taxes
            'total_included': 0.0,    # Total with taxes
            'taxes': [{               # One dict for each tax in self
                                      # and their children
                'id': int,
                'name': str,
                'amount': float,
                'sequence': int,
                'account_id': int,
                'refund_account_id': int,
                'analytic': boolean,
            }]
        }"""

        taxes_results = super().compute_all(
            price_unit,
            currency,
            quantity,
            product,
            partner,
            is_refund,
            handle_price_include,
            include_caba_tags,
            rounding_method,
        )

        if not fiscal_taxes:
            fiscal_taxes = self.env["l10n_br_fiscal.tax"]

        product = product or self.env["product.product"]

        if len(self) == 0:
            company = self.env.company
            if self.env.context.get("default_company_id") or self.env.context.get(
                "allowed_company_ids"
            ):
                company = self.env["res.company"].browse(
                    self.env.context.get("default_company_id")
                    or self.env.context.get("allowed_company_ids")[0]
                )
        else:
            company = self[0].company_id

        fiscal_taxes_results = fiscal_taxes.compute_taxes(
            company=company,
            partner=partner,
            product=product,
            price_unit=price_unit,
            quantity=quantity,
            uom_id=product.uom_id,
            fiscal_price=fiscal_price or price_unit,
            fiscal_quantity=fiscal_quantity or quantity,
            uot_id=uot_id or product.uot_id,
            ncm=ncm or product.ncm_id,
            nbs=nbs or product.nbs_id,
            nbm=nbm or product.nbm_id,
            cest=cest or product.cest_id,
            cfop=cfop,
            discount_value=discount_value,
            insurance_value=insurance_value,
            other_value=other_value,
            ii_customhouse_charges=ii_customhouse_charges,
            freight_value=freight_value,
            operation_line=operation_line,
            icmssn_range=icmssn_range,
            icms_origin=icms_origin or product.icms_origin,
            ind_final=ind_final,
        )

        taxes_results["amount_tax_included"] = fiscal_taxes_results["amount_included"]
        taxes_results["amount_tax_not_included"] = fiscal_taxes_results[
            "amount_not_included"
        ]
        taxes_results["amount_tax_withholding"] = fiscal_taxes_results[
            "amount_withholding"
        ]
        taxes_results["amount_estimate_tax"] = fiscal_taxes_results["estimate_tax"]

        account_taxes_by_domain = {}

        sign = -1 if fixed_multiplicator < 0 else 1

        for tax in self:
            tax_domain = tax.tax_group_id.fiscal_tax_group_id.tax_domain
            account_taxes_by_domain.update({tax.id: tax_domain})

        for account_tax in taxes_results["taxes"]:
            tax = self.filtered(lambda t: t.id == account_tax.get("id"))  # noqa: B023
            fiscal_tax = fiscal_taxes_results["taxes"].get(
                account_taxes_by_domain.get(tax.id)
            )

            account_tax.update(
                {
                    "tax_group_id": tax.tax_group_id.id,
                    "deductible": tax.deductible,
                }
            )

            tax_repartition_lines = (
                is_refund
                and tax.refund_repartition_line_ids
                or tax.invoice_repartition_line_ids
            ).filtered(lambda x: x.repartition_type == "tax")

            sum_repartition_factor = sum(tax_repartition_lines.mapped("factor"))

            if fiscal_tax:
                if fiscal_tax.get("base") < 0:
                    sign = -1
                    fiscal_tax["base"] = -fiscal_tax.get("base")

                if not fiscal_tax.get("tax_include") and not tax.deductible:
                    taxes_results["total_included"] += fiscal_tax.get("tax_value")

                fiscal_group = tax.tax_group_id.fiscal_tax_group_id
                tax_amount = fiscal_tax.get("tax_value", 0.0) * sum_repartition_factor
                tax_base = fiscal_tax.get("base") * sum_repartition_factor
                if tax.deductible or fiscal_group.tax_withholding:
                    tax_amount = (
                        fiscal_tax.get("tax_value", 0.0) * sum_repartition_factor
                    )

                account_tax.update(
                    {
                        "id": account_tax.get("id"),
                        "name": fiscal_group.name,
                        "fiscal_name": fiscal_tax.get("name"),
                        "base": tax_base * sign,
                        "tax_include": fiscal_tax.get("tax_include"),
                        "amount": tax_amount * sign,
                        "fiscal_tax_id": fiscal_tax.get("fiscal_tax_id"),
                        "tax_withholding": fiscal_group.tax_withholding,
                    }
                )

        return taxes_results

    @api.model
    def _compute_taxes_for_single_line(
        self,
        base_line,
        handle_price_include=True,
        include_caba_tags=False,
        early_pay_discount_computation=None,
        early_pay_discount_percentage=None,
    ):
        """
        DISABLED for Odoo 18.0+

        This method was overriding the core _compute_taxes_for_single_line which was
        called during dynamic line sync to compute taxes for each line. In Odoo 18,
        this method no longer exists in the core account module.

        Brazilian tax computation is now handled through the _compute_totals method
        and the _add_tax_details_in_base_line flow.

        Similar to the _compute_taxes_for_single_line super method in the account module
        but overriden to pass extra parameters to the account.tax compule_all method
        to compute taxes properly in Brazil.
        """
        # In Odoo 18, this method doesn't exist in the core module.
        # Return empty result to avoid breaking the chain.
        # TODO: Remove this method entirely after confirming it's not needed.
        return {}, []

    def _add_tax_details_in_base_line(self, base_line, company, rounding_method=None):
        """Override to inject Brazilian fiscal tax computation.

        In Odoo 18, this method replaces the old _compute_all_tax flow.
        It computes taxes and stores them in base_line['tax_details'].
        We override it to use the Brazilian tax engine when fiscal_operation_id
        is present on the record.
        """
        record = base_line.get("record")

        # Check if this is a Brazilian fiscal line
        if (
            record
            and hasattr(record, "fiscal_operation_id")
            and record.fiscal_operation_id
        ):
            # Use Brazilian tax computation
            self._add_br_tax_details_in_base_line(base_line, company, rounding_method)
        else:
            # Use standard tax computation
            super()._add_tax_details_in_base_line(base_line, company, rounding_method)
        return None

    def _add_br_tax_details_in_base_line(
        self, base_line, company, rounding_method=None
    ):
        """Compute Brazilian taxes and add them to base_line['tax_details']."""
        record = base_line.get("record")
        if not record or not hasattr(record, "fiscal_tax_ids"):
            super()._add_tax_details_in_base_line(base_line, company, rounding_method)
            return

        # Check if we have valid Brazilian fiscal data
        try:
            if not record.exists():
                super()._add_tax_details_in_base_line(
                    base_line, company, rounding_method
                )
                return
            if not record.fiscal_operation_id or not record.fiscal_operation_line_id:
                super()._add_tax_details_in_base_line(
                    base_line, company, rounding_method
                )
                return
        except Exception:
            super()._add_tax_details_in_base_line(base_line, company, rounding_method)
            return

        # First, compute standard tax details to get proper structure
        super()._add_tax_details_in_base_line(base_line, company, rounding_method)

        # Then override with Brazilian fiscal computation
        fiscal_taxes = record.fiscal_tax_ids
        if not fiscal_taxes:
            return  # Keep standard computation

        rounding_method = rounding_method or company.tax_calculation_rounding_method
        price_unit_after_discount = base_line["price_unit"] * (
            1 - (base_line["discount"] / 100.0)
        )
        currency = base_line["currency_id"]
        rate = base_line.get("rate", 1.0)

        # Compute Brazilian fiscal taxes
        # Handle different tax field names:
        # tax_ids for account.move.line, tax_id for sale.order.line
        tax_ids = getattr(record, "tax_ids", None) or getattr(record, "tax_id", None)
        if not tax_ids:
            super()._add_tax_details_in_base_line(base_line, company, rounding_method)
            return
        taxes_computation = tax_ids._origin.compute_all(
            price_unit=price_unit_after_discount,
            currency=currency,
            quantity=base_line["quantity"],
            product=base_line.get("product_id"),
            partner=base_line.get("partner_id"),
            is_refund=base_line.get("is_refund", False),
            handle_price_include=base_line.get("handle_price_include", True),
            include_caba_tags=False,
            rounding_method=rounding_method,
            fiscal_taxes=fiscal_taxes,
            operation_line=record.fiscal_operation_line_id,
            cfop=record.cfop_id or None,
            ncm=record.ncm_id,
            nbs=record.nbs_id,
            nbm=record.nbm_id,
            cest=record.cest_id,
            discount_value=record.discount_value,
            insurance_value=record.insurance_value,
            other_value=record.other_value,
            ii_customhouse_charges=record.ii_customhouse_charges,
            freight_value=record.freight_value,
            fiscal_price=record.fiscal_price,
            fiscal_quantity=record.fiscal_quantity,
            uot_id=record.uot_id,
            icmssn_range=record.icmssn_range_id,
            icms_origin=record.icms_origin,
            ind_final=record.ind_final,
        )

        # Override totals with Brazilian computation
        tax_details = base_line["tax_details"]

        tax_details["raw_total_excluded_currency"] = taxes_computation["total_excluded"]
        tax_details["raw_total_excluded"] = (
            taxes_computation["total_excluded"] / rate if rate else 0.0
        )
        tax_details["raw_total_included_currency"] = taxes_computation["total_included"]
        tax_details["raw_total_included"] = (
            taxes_computation["total_included"] / rate if rate else 0.0
        )

        if rounding_method == "round_per_line":
            tax_details["raw_total_excluded"] = company.currency_id.round(
                tax_details["raw_total_excluded"]
            )
            tax_details["raw_total_included"] = company.currency_id.round(
                tax_details["raw_total_included"]
            )

        # Override individual tax amounts if we have matching taxes
        br_taxes_by_id = {t["id"]: t for t in taxes_computation["taxes"]}
        for tax_data in tax_details["taxes_data"]:
            tax = tax_data["tax"]
            if tax.id in br_taxes_by_id:
                br_tax = br_taxes_by_id[tax.id]
                tax_data["tax_amount"] = br_tax["amount"]
                tax_data["base"] = br_tax["base"]
                tax_data["raw_tax_amount_currency"] = br_tax["amount"]
                tax_data["raw_tax_amount"] = br_tax["amount"] / rate if rate else 0.0
                tax_data["raw_base_amount_currency"] = br_tax["base"]
                tax_data["raw_base_amount"] = br_tax["base"] / rate if rate else 0.0

    @api.model
    def _get_tax_totals_summary(
        self, base_lines, currency, company, cash_rounding=None
    ):
        res = super()._get_tax_totals_summary(
            base_lines, currency, company, cash_rounding
        )
        amount_total = res["total_amount_currency"]

        for line in base_lines:
            if line.get("record") and hasattr(
                line["record"], "fiscal_operation_line_id"
            ):
                amount_total = line["record"]._get_total_for_tax_totals()
                break

        res["formatted_amount_total"] = formatLang(
            self.env,
            amount_total,
            currency_obj=currency,
        )

        return res
