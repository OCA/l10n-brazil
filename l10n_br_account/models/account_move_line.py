# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from contextlib import contextmanager

from odoo import Command, _, api, fields, models
from odoo.tools import frozendict


class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _fiscal_decorator_model = "l10n_br_fiscal.document.line"
    _fiscal_decorator_compute_blacklist = ["_compute_fiscal_amounts"]
    _inherit = [
        _name,
        "l10n_br_fiscal.document.line.mixin.methods",
        "l10n_br_account.decorator.mixin",
    ]
    _inherits = {_fiscal_decorator_model: "fiscal_document_line_id"}

    fiscal_document_line_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.line",
        string="Fiscal Document Line",
        copy=False,
        ondelete="cascade",
    )

    document_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.type",
        related="move_id.document_type_id",
    )

    discount = fields.Float(
        compute="_compute_discounts",
        store=True,
    )

    payment_term_number = fields.Char(
        help="Stores the installment number in the format 'current-total'. "
        "For example, '1-3' for the first of three installments, '2-3' for the second,"
        " and '3-3' for the last installment.",
    )

    # -------------------------------------------------------------------------
    # SHADOWED FIELDS SYNC
    # These fields have the same name in account.move.line
    # and l10n_br_fiscal.document.line. So they wouldn't get updated
    # by the _inherits system. An alternative would be changing their name
    # in l10n_br_fiscal but that would make the code unreadable and fiscal mixin
    # methods would fail to do what we expect from them in the Odoo objects.
    # -------------------------------------------------------------------------

    name = fields.Char(inverse="_inverse_name")
    quantity = fields.Float(inverse="_inverse_quantity")
    price_unit = fields.Float(inverse="_inverse_price_unit")

    @api.onchange("product_id")
    def _inverse_product_id(self):
        for line in self:
            if line.fiscal_document_line_id:
                line.fiscal_document_line_id.product_id = line.product_id.id
        return super()._inverse_product_id()

    @api.onchange("name")
    def _inverse_name(self):
        for line in self:
            if line.fiscal_document_line_id:
                line.fiscal_document_line_id.name = line.name

    @api.onchange("quantity")
    def _inverse_quantity(self):
        for line in self:
            if line.fiscal_document_line_id:
                line.fiscal_document_line_id.quantity = line.quantity

    @api.onchange("price_unit")
    def _inverse_price_unit(self):
        for line in self:
            if line.fiscal_document_line_id:
                line.fiscal_document_line_id.price_unit = line.price_unit

    @api.depends(
        "quantity",
        "price_unit",
        "discount_value",
    )
    def _compute_discounts(self):
        for line in self:
            line.discount = (line.discount_value * 100) / (
                line.quantity * line.price_unit or 1
            )

    @api.depends("product_id", "payment_term_number")
    def _compute_name(self):
        """
        Override to set 'name' with 'document_number/payment_term_number' for
        payment term lines. For other lines, it calls the superclass method.
        """
        payment_term_lines = self.filtered(
            lambda line: line.display_type == "payment_term"
            and line.document_type_id
            and line.move_id.document_number
            and line.payment_term_number
        )
        for line in payment_term_lines:
            # set label for payment term lines. Ex: '0001/1-3'
            line.name = f"{line.move_id.document_number}/{line.payment_term_number}"

        other_lines = self - payment_term_lines
        if other_lines:
            return super()._compute_name()
        return True

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if values.get("fiscal_document_line_id"):
                continue

            move_id = self.env["account.move"].browse(values["move_id"])
            fiscal_doc_id = move_id.fiscal_document_id.id
            if not fiscal_doc_id:
                continue
            values["document_id"] = fiscal_doc_id  # pass through the _inherits system
        # This reordering bellow is crucial to ensure accurate linkage between
        # account.move.line (aml) and the fiscal document line. In the fiscal create a
        # fiscal document line, leaving only those that should be created. Proper
        # ordering is essential as mismatches between the order of amls and the
        # manipulated vals_list of fiscal documents can lead to incorrect linkages.
        # For example, if vals_list[0] in amls does not match vals_list[0] in the
        # fiscal document (which is a manipulated vals_list), it results in erroneous
        # associations.

        # Add index to each dictionary in vals_list
        indexed_vals_list = [(idx, val) for idx, val in enumerate(vals_list)]

        # Reorder vals_list so lines with fiscal_operation_line_id will
        # be created first
        sorted_indexed_vals_list = sorted(
            indexed_vals_list,
            key=lambda x: not x[1].get("fiscal_operation_line_id"),
        )
        original_indexes = [idx for idx, _ in sorted_indexed_vals_list]
        vals_list = [val for _, val in sorted_indexed_vals_list]

        # Create the records
        result = super().create(vals_list)

        # Initialize the inverted index list with the same length as the original list
        inverted_index = [0] * len(original_indexes)

        # Iterate over the original_indexes list and fill the inverted_index list
        #  accordingly
        for i, val in enumerate(original_indexes):
            inverted_index[val] = i

        # Re-order the result according to the initial vals_list order
        sorted_result = self.env["account.move.line"]
        for idx in inverted_index:
            sorted_result |= result[idx]
        return sorted_result

    def unlink(self):
        unlink_fiscal_lines = self.env["l10n_br_fiscal.document.line"]
        for inv_line in self:
            if not inv_line.exists():
                continue
            if inv_line.fiscal_document_line_id:
                unlink_fiscal_lines |= inv_line.fiscal_document_line_id
        result = super().unlink()
        unlink_fiscal_lines.unlink()
        self.clear_caches()
        return result

    @contextmanager
    def _sync_invoice(self, container):
        """
        Almost the same as the super method from the account module.
        The changes are after the comment "# BRAZIL CASE:"
        WARNING: sadly it seems we may not be able to call the super method...
        """
        if container["records"].env.context.get("skip_invoice_line_sync"):
            yield
            return  # avoid infinite recursion

        def existing():
            return {
                line: {
                    "amount_currency": line.currency_id.round(line.amount_currency),
                    "balance": line.company_id.currency_id.round(line.balance),
                    "currency_rate": line.currency_rate,
                    "price_subtotal": line.currency_id.round(line.price_subtotal),
                    "move_type": line.move_id.move_type,
                }
                for line in container["records"]
                .with_context(
                    skip_invoice_line_sync=True,
                )
                .filtered(lambda line: line.move_id.is_invoice(True))
            }

        def changed(fname):
            return line not in before or before[line][fname] != after[line][fname]

        before = existing()
        yield
        after = existing()
        for line in after:
            if (
                line.display_type == "product"
                and not self.env.is_protected(self._fields["amount_currency"], line)
                and (not changed("amount_currency") or line not in before)
            ):
                if not line.move_id.fiscal_operation_id:
                    unsigned_amount_currency = line.currency_id.round(
                        line.price_subtotal
                    )
                else:  # BRAZIL CASE:
                    if line.cfop_id and not line.cfop_id.finance_move:
                        unsigned_amount_currency = 0
                        if not line.move_id.fiscal_operation_id.deductible_taxes:
                            # When there is no financial amount but there are non
                            # dectutible taxes, then we should take the total tax
                            # amount into account here to keep the move balanced.
                            # (In v14 that was done automatically in the payment terms)
                            unsigned_amount_currency = -(
                                line.amount_tax_included
                                + line.amount_tax_not_included
                                - line.amount_tax_withholding
                            )
                    else:
                        if line.move_id.fiscal_operation_id.deductible_taxes:
                            unsigned_amount_currency = (
                                line.amount_total + line.amount_tax_withholding
                            )
                        else:
                            amount_total = (
                                line.amount_total + line.amount_tax_withholding
                            )
                            unsigned_amount_currency = line.currency_id.round(
                                amount_total
                                - line.amount_tax_included
                                - line.amount_tax_not_included
                                if line.tax_ids
                                else amount_total
                            )

                amount_currency = unsigned_amount_currency * line.move_id.direction_sign

                if line.amount_currency != amount_currency or line not in before:
                    line.amount_currency = amount_currency
                if line.currency_id == line.company_id.currency_id:
                    line.balance = amount_currency

        after = existing()
        for line in after:
            if (
                (
                    changed("amount_currency")
                    or changed("currency_rate")
                    or changed("move_type")
                )
                and not self.env.is_protected(self._fields["balance"], line)
                and (
                    not changed("balance") or (line not in before and not line.balance)
                )
            ):
                balance = line.company_id.currency_id.round(
                    line.amount_currency / line.currency_rate
                )
                line.balance = balance

        # Since this method is called during the sync,
        # inside of `create`/`write`, these fields
        # already have been computed and marked as so.
        # But this method should re-trigger it since
        # it changes the dependencies.
        self.env.add_to_compute(self._fields["debit"], container["records"])
        self.env.add_to_compute(self._fields["credit"], container["records"])

    @api.depends(
        "quantity",
        "discount",
        "price_unit",
        "tax_ids",
        "currency_id",
        "discount",
        "fiscal_tax_ids",
        "fiscal_operation_line_id",
        "cfop_id",
        "ncm_id",
        "nbs_id",
        "nbm_id",
        "cest_id",
        "discount_value",
        "insurance_value",
        "other_value",
        "ii_customhouse_charges",
        "freight_value",
        "fiscal_price",
        "fiscal_quantity",
        "uot_id",
        "icmssn_range_id",
        "icms_origin",
        "ind_final",
    )
    def _compute_totals(self):
        """
        Overriden to pass all the Brazilian parameters we need
        to the account.tax#compute_all method.
        """
        result = super(
            AccountMoveLine,
            self.with_context(
                skip_compute_fiscal_tax_ids=True, skip_compute_tax_fields=True
            ),
        )._compute_totals()
        if not self.move_id.fiscal_operation_id:
            return result

        for line in self:
            if line.display_type != "product":
                continue  # handled in super method

            line_discount_price_unit = line.price_unit * (1 - (line.discount / 100.0))

            # Compute 'price_total'.
            if line.tax_ids:
                taxes_res = line.tax_ids._origin.with_context().compute_all(
                    line_discount_price_unit,
                    currency=line.currency_id,
                    quantity=line.quantity,
                    product=line.product_id,
                    partner=line.partner_id,
                    is_refund=line.move_type in ("out_refund", "in_refund"),
                    handle_price_include=True,  # sure?
                    fiscal_taxes=line.with_context(
                        skip_compute_fiscal_tax_ids=True
                    ).fiscal_tax_ids,
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

                line.price_subtotal = taxes_res["total_excluded"]
                line.price_total = taxes_res["total_included"]

            line.price_total += (
                line.insurance_value
                + line.other_value
                + line.freight_value
                - line.icms_relief_value
            )
        return result

    @api.depends(
        "tax_ids",
        "currency_id",
        "partner_id",
        "analytic_distribution",
        "balance",
        "partner_id",
        "move_id.partner_id",
        "price_unit",
        "fiscal_tax_ids",
        "fiscal_operation_line_id",
        "cfop_id",
        "ncm_id",
        "nbm_id",
        "nbs_id",
        "cest_id",
        "discount_value",
        "insurance_value",
        "other_value",
        "ii_customhouse_charges",
        "freight_value",
        "fiscal_price",
        "fiscal_quantity",
        "uot_id",
        "icmssn_range_id",
        "icms_origin",
        "ind_final",
    )
    def _compute_all_tax(self):
        """
        Overriden to pass all the extra Brazilian parameters we need
        to the account.tax#compute_all method.
        """
        if not self.move_id.fiscal_operation_id:
            return super()._compute_all_tax()

        for line in self:
            sign = line.move_id.direction_sign
            if line.display_type == "tax":
                line.compute_all_tax = {}
                line.compute_all_tax_dirty = False
                continue
            if line.display_type == "product" and line.move_id.is_invoice(True):
                amount_currency = sign * line.price_unit * (1 - line.discount / 100)
                handle_price_include = True
                quantity = line.quantity
            else:
                amount_currency = line.amount_currency
                handle_price_include = False
                quantity = 1
            compute_all_currency = line.tax_ids.compute_all(
                amount_currency,
                currency=line.currency_id,
                quantity=quantity,
                product=line.product_id,
                partner=line.move_id.partner_id or line.partner_id,
                is_refund=line.is_refund,
                handle_price_include=handle_price_include,
                include_caba_tags=line.move_id.always_tax_exigible,
                fixed_multiplicator=sign,
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
            rate = (
                line.amount_currency / line.balance
                if (line.balance and line.amount_currency)
                else 1
            )
            line.compute_all_tax_dirty = True
            line.compute_all_tax = {
                frozendict(
                    {
                        "tax_repartition_line_id": tax["tax_repartition_line_id"],
                        "group_tax_id": tax["group"] and tax["group"].id or False,
                        "account_id": tax["account_id"] or line.account_id.id,
                        "currency_id": line.currency_id.id,
                        "analytic_distribution": (
                            tax["analytic"] or not tax["use_in_tax_closing"]
                        )
                        and line.analytic_distribution,
                        "tax_ids": [Command.set(tax["tax_ids"])],
                        "tax_tag_ids": [Command.set(tax["tag_ids"])],
                        "partner_id": line.move_id.partner_id.id or line.partner_id.id,
                        "move_id": line.move_id.id,
                        "display_type": line.display_type,
                    }
                ): {
                    "name": tax["name"]
                    + (" " + _("(Discount)") if line.display_type == "epd" else ""),
                    "balance": tax["amount"] / rate,
                    "amount_currency": tax["amount"],
                    "tax_base_amount": tax["base"]
                    / rate
                    * (-1 if line.tax_tag_invert else 1),
                }
                for tax in compute_all_currency["taxes"]
                if tax["amount"]
            }
            if not line.tax_repartition_line_id:
                line.compute_all_tax[frozendict({"id": line.id})] = {
                    "tax_tag_ids": [Command.set(compute_all_currency["base_tags"])],
                }

    @api.onchange("fiscal_document_line_id")
    def _onchange_fiscal_document_line_id(self):
        if self.fiscal_document_line_id:
            # do the onchange dance for fields with the same names:
            self.product_id = self.fiscal_document_line_id.product_id.id
            self.name = self.fiscal_document_line_id.name
            self.quantity = self.fiscal_document_line_id.quantity
            self.price_unit = self.fiscal_document_line_id.price_unit
            # override the default product uom (set by the onchange):
            self.product_uom_id = self.fiscal_document_line_id.uom_id.id

    @api.depends("product_id", "product_uom_id", "fiscal_tax_ids")
    def _compute_tax_ids(self):
        # Adding 'fiscal_tax_ids' as a dependency to ensure that the taxes
        # are recalculated when this field changes.
        return super()._compute_tax_ids()

    def _get_computed_taxes(self):
        """
        Override the native method to load taxes from the fiscal module.
        """
        self.ensure_one()

        # If no fiscal operation is defined, fallback to the default implementation.
        if not self.fiscal_operation_id:
            return super()._get_computed_taxes()

        # Determine the user type based on the document type.
        user_type = None
        if self.move_id.is_sale_document(include_receipts=True):
            user_type = "sale"
        elif self.move_id.is_purchase_document(include_receipts=True):
            user_type = "purchase"

        return self.fiscal_tax_ids.account_taxes(
            user_type=user_type,
            fiscal_operation=self.fiscal_operation_id,
            company=self.company_id,
        )

    @api.constrains("product_uom_id")
    def _check_product_uom_category_id(self):
        not_imported = self.filtered(lambda line: not line._is_imported())
        return super(AccountMoveLine, not_imported)._check_product_uom_category_id()
