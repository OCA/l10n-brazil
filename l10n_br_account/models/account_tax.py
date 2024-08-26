# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import Command, api, fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import FINAL_CUSTOMER_NO


class AccountTax(models.Model):
    _inherit = "account.tax"

    fiscal_tax_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.tax",
        relation="fiscal_account_tax_rel",
        column1="account_tax_id",
        column2="fiscal_tax_id",
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
            fixed_multiplicator,
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
            tax = self.filtered(lambda t: t.id == account_tax.get("id"))
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
        Similar to the _compute_taxes_for_single_line super method in the account module
        but overriden to pass extra parameters to the account.tax compule_all method
        to compute taxes properly in Brazil.
        WARNING: it seems we might not be able to call the super method here...
        """
        orig_price_unit_after_discount = base_line["price_unit"] * (
            1 - (base_line["discount"] / 100.0)
        )
        price_unit_after_discount = orig_price_unit_after_discount
        taxes = base_line["taxes"]._origin
        currency = base_line["currency"] or self.env.company.currency_id
        rate = base_line["rate"]

        if early_pay_discount_computation in ("included", "excluded"):
            remaining_part_to_consider = (100 - early_pay_discount_percentage) / 100.0
            price_unit_after_discount = (
                remaining_part_to_consider * price_unit_after_discount
            )

        if taxes:
            line = base_line["record"]
            taxes_res = taxes.with_context(**base_line["extra_context"]).compute_all(
                price_unit_after_discount,
                currency=currency,
                quantity=base_line["quantity"],
                product=base_line["product"],
                partner=base_line["partner"],
                is_refund=base_line["is_refund"],
                handle_price_include=base_line["handle_price_include"],
                include_caba_tags=include_caba_tags,
                fiscal_taxes=line.fiscal_tax_ids,
                operation_line=line.fiscal_operation_line_id,
                cfop=line.cfop_id or None,
                ncm=line.ncm_id,
                nbs=line.nbs_id,
                nbm=line.nbm_id,
                cest=line.cest_id,
                discount_value=line.discount_value,
                insurance_value=line.insurance_value,
                other_value=line.other_value,
                ii_customhouse_charges=line.ii_customhouse_charges,
                freight_value=line.freight_value,
                fiscal_price=line.fiscal_price,
                fiscal_quantity=line.fiscal_quantity,
                uot_id=line.uot_id,
                icmssn_range=line.icmssn_range_id,
                icms_origin=line.icms_origin,
                ind_final=line.ind_final,
            )

            to_update_vals = {
                "tax_tag_ids": [Command.set(taxes_res["base_tags"])],
                "price_subtotal": taxes_res["total_excluded"],
                "price_total": taxes_res["total_included"],
            }

            if early_pay_discount_computation == "excluded":
                new_taxes_res = taxes.with_context(
                    **base_line["extra_context"]
                ).compute_all(
                    orig_price_unit_after_discount,
                    currency=currency,
                    quantity=base_line["quantity"],
                    product=base_line["product"],
                    partner=base_line["partner"],
                    is_refund=base_line["is_refund"],
                    handle_price_include=base_line["handle_price_include"],
                    include_caba_tags=include_caba_tags,
                )
                for tax_res, new_taxes_res in zip(
                    taxes_res["taxes"], new_taxes_res["taxes"]
                ):
                    delta_tax = new_taxes_res["amount"] - tax_res["amount"]
                    tax_res["amount"] += delta_tax
                    to_update_vals["price_total"] += delta_tax

            tax_values_list = []
            for tax_res in taxes_res["taxes"]:
                tax_amount = tax_res["amount"] / rate
                if self.company_id.tax_calculation_rounding_method == "round_per_line":
                    tax_amount = currency.round(tax_amount)
                tax_rep = self.env["account.tax.repartition.line"].browse(
                    tax_res["tax_repartition_line_id"]
                )
                tax_values_list.append(
                    {
                        **tax_res,
                        "tax_repartition_line": tax_rep,
                        "base_amount_currency": tax_res["base"],
                        "base_amount": currency.round(tax_res["base"] / rate),
                        "tax_amount_currency": tax_res["amount"],
                        "tax_amount": tax_amount,
                    }
                )

        else:
            price_subtotal = currency.round(
                price_unit_after_discount * base_line["quantity"]
            )
            to_update_vals = {
                "tax_tag_ids": [Command.clear()],
                "price_subtotal": price_subtotal,
                "price_total": price_subtotal,
            }
            tax_values_list = []

        return to_update_vals, tax_values_list
