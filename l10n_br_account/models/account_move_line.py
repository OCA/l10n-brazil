# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
# pylint: disable=api-one-deprecated

from odoo import api, fields, models

from .account_move import InheritsCheckMuteLogger

# These fields have the same name in account.move.line
# and l10n_br_fiscal.document.line. So they wouldn't get updated
# by the _inherits system. An alternative would be changing their name
# in l10n_br_fiscal but that would make the code unreadable and fiscal mixin
# methods would fail to do what we expect from them in the Odoo objects
# where they are injected.
# Fields that are related in l10n_br_fiscal.document.line like partner_id or company_id
# don't need to be written through the account.move.line write.
SHADOWED_FIELDS = [
    "product_id",
    "name",
    "quantity",
    "price_unit",
]

ACCOUNTING_FIELDS = ("debit", "credit", "amount_currency")
BUSINESS_FIELDS = ("price_unit", "quantity", "discount", "tax_ids")


class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _inherit = [_name, "l10n_br_fiscal.document.line.mixin.methods"]
    _inherits = {"l10n_br_fiscal.document.line": "fiscal_document_line_id"}

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

    tax_framework = fields.Selection(
        related="move_id.company_id.tax_framework",
        string="Tax Framework",
    )

    cfop_destination = fields.Selection(
        related="cfop_id.destination", string="CFOP Destination"
    )

    partner_company_type = fields.Selection(related="partner_id.company_type")

    ind_final = fields.Selection(related="move_id.ind_final")

    fiscal_genre_code = fields.Char(
        related="fiscal_genre_id.code",
        string="Fiscal Product Genre Code",
    )

    # The following fields belong to the fiscal document line mixin
    # but they are redefined here to ensure they are recomputed in the
    # account.move.line views.
    icms_cst_code = fields.Char(
        related="icms_cst_id.code",
        string="ICMS CST Code",
    )

    ipi_cst_code = fields.Char(
        related="ipi_cst_id.code",
        string="IPI CST Code",
    )

    cofins_cst_code = fields.Char(
        related="cofins_cst_id.code",
        string="COFINS CST Code",
    )

    cofinsst_cst_code = fields.Char(
        related="cofinsst_cst_id.code",
        string="COFINS ST CST Code",
    )

    pis_cst_code = fields.Char(
        related="pis_cst_id.code",
        string="PIS CST Code",
    )

    pisst_cst_code = fields.Char(
        related="pisst_cst_id.code",
        string="PIS ST CST Code",
    )

    partner_is_public_entity = fields.Boolean(related="partner_id.is_public_entity")

    allow_csll_irpj = fields.Boolean(
        compute="_compute_allow_csll_irpj",
    )

    discount = fields.Float(
        compute="_compute_discounts",
        store=True,
    )

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

    @api.model
    def _inherits_check(self):
        """
        Overriden to avoid the super method to set the fiscal_document_line_id
        field as required.
        """
        with InheritsCheckMuteLogger("odoo.models"):  # mute spurious warnings
            res = super()._inherits_check()
        field = self._fields.get("fiscal_document_line_id")
        field.required = False  # unset the required = True assignement
        return res

    @api.model
    def _shadowed_fields(self):
        """Return the list of shadowed fields that are synchronized
        from account.move.line."""
        return SHADOWED_FIELDS

    @api.model
    def _inject_shadowed_fields(self, vals_list):
        for vals in vals_list:
            for field in self._shadowed_fields():
                if field in vals:
                    vals["fiscal_proxy_%s" % (field,)] = vals[field]

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if values.get("fiscal_document_line_id"):
                fiscal_line_data = (
                    self.env["l10n_br_fiscal.document.line"]
                    .browse(values["fiscal_document_line_id"])
                    .read(self._shadowed_fields())[0]
                )
                for k, v in fiscal_line_data.items():
                    if isinstance(v, tuple):  # m2o
                        values[k] = v[0]
                    else:
                        values[k] = v
                continue

            if values.get("exclude_from_invoice_tab"):
                continue

            move_id = self.env["account.move"].browse(values["move_id"])
            fiscal_doc_id = move_id.fiscal_document_id.id

            if not fiscal_doc_id:
                continue

            values.update(
                self._update_fiscal_quantity(
                    values.get("product_id"),
                    values.get("price_unit"),
                    values.get("quantity"),
                    values.get("product_uom_id"),
                    values.get("uot_id"),
                )
            )
            if values.get("product_uom_id"):
                values["uom_id"] = values["product_uom_id"]
            values["document_id"] = fiscal_doc_id  # pass through the _inherits system

            if (
                move_id.is_invoice(include_receipts=True)
                and move_id.company_id.country_id.code == "BR"
                and any(
                    values.get(field)
                    for field in [*ACCOUNTING_FIELDS, *BUSINESS_FIELDS]
                )
            ):
                fisc_values = {
                    key: values[key]
                    for key in self.env["l10n_br_fiscal.document.line"]._fields.keys()
                    if values.get(key)
                }
                fiscal_line = self.env["l10n_br_fiscal.document.line"].new(fisc_values)
                fiscal_line._compute_amounts()
                cfop = values.get("cfop_id")
                cfop_id = (
                    self.env["l10n_br_fiscal.cfop"].browse(cfop) if cfop else False
                )
                values.update(
                    self._get_amount_credit_debit_model(
                        move_id,
                        exclude_from_invoice_tab=values.get(
                            "exclude_from_invoice_tab", False
                        ),
                        amount_tax_included=values.get("amount_tax_included", 0),
                        amount_tax_not_included=values.get(
                            "amount_tax_not_included", 0
                        ),
                        amount_tax_withholding=values.get("amount_tax_withholding", 0),
                        amount_total=fiscal_line.amount_total,
                        currency_id=move_id.currency_id,
                        company_id=move_id.company_id,
                        date=move_id.date,
                        cfop_id=cfop_id,
                    )
                )
        self._inject_shadowed_fields(vals_list)

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
        result = super(
            AccountMoveLine, self.with_context(create_from_move_line=True)
        ).create(vals_list)

        # Initialize the inverted index list with the same length as the original list
        inverted_index = [0] * len(original_indexes)

        # Iterate over the original_indexes list and fill the inverted_index list accordingly
        for i, val in enumerate(original_indexes):
            inverted_index[val] = i

        # Re-order the result according to the initial vals_list order
        sorted_result = self.env["account.move.line"]
        for idx in inverted_index:
            sorted_result |= result[idx]

        for line in sorted_result:
            # Forces the recalculation of price_total and price_subtotal fields which are
            # recalculated by super
            if line.move_id.company_id.country_id.code == "BR":
                line.update(line._get_price_total_and_subtotal())

        return sorted_result

    def write(self, values):
        if values.get("product_uom_id"):
            values["uom_id"] = values["product_uom_id"]
        non_dummy = self.filtered(lambda line: line.fiscal_document_line_id)
        self._inject_shadowed_fields([values])
        if values.get("move_id") and len(non_dummy) == len(self):
            # we can write the document_id in all lines
            values["document_id"] = (
                self.env["account.move"].browse(values["move_id"]).fiscal_document_id.id
            )
            result = super().write(values)
        elif values.get("move_id"):
            # we will only define document_id for non dummy lines
            result = super().write(values)
            doc_id = (
                self.env["account.move"].browse(values["move_id"]).fiscal_document_id.id
            )
            super(AccountMoveLine, non_dummy).write({"document_id": doc_id})
        else:
            result = super().write(values)

        for line in self:
            cleaned_vals = line.move_id._cleanup_write_orm_values(line, values)
            if not cleaned_vals:
                continue

            if not line.move_id.is_invoice(include_receipts=True):
                continue

            if any(
                field in cleaned_vals
                for field in [*ACCOUNTING_FIELDS, *BUSINESS_FIELDS]
            ):
                to_write = line._get_amount_credit_debit_model(
                    line.move_id,
                    exclude_from_invoice_tab=line.exclude_from_invoice_tab,
                    amount_tax_included=line.amount_tax_included,
                    amount_tax_not_included=line.amount_tax_not_included,
                    amount_tax_withholding=line.amount_tax_withholding,
                    amount_total=line.amount_total,
                    currency_id=line.currency_id,
                    company_id=line.company_id,
                    date=line.date,
                    cfop_id=line.cfop_id,
                )
                result |= super(AccountMoveLine, line).write(to_write)

        return result

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

    # TODO As the accounting behavior of taxes in Brazil is completely different,
    # for now the method for companies in Brazil brings an empty result.
    # You can correctly map this behavior later.
    @api.model
    def _get_fields_onchange_balance_model(
        self,
        quantity,
        discount,
        amount_currency,
        move_type,
        currency,
        taxes,
        price_subtotal,
        force_computation=False,
    ):
        res = super()._get_fields_onchange_balance_model(
            quantity=quantity,
            discount=discount,
            amount_currency=amount_currency,
            move_type=move_type,
            currency=currency,
            taxes=taxes,
            price_subtotal=price_subtotal,
            force_computation=force_computation,
        )
        if (self.env.company.country_id.code == "BR") and (
            not self.exclude_from_invoice_tab and "price_unit" in res
        ):
            res = {}

        return res

    def _get_price_total_and_subtotal(
        self,
        price_unit=None,
        quantity=None,
        discount=None,
        currency=None,
        product=None,
        partner=None,
        taxes=None,
        move_type=None,
    ):
        self.ensure_one()
        return super(
            AccountMoveLine,
            self.with_context(
                partner_id=self.partner_id,
                product_id=self.product_id,
                fiscal_tax_ids=self.fiscal_tax_ids,
                fiscal_operation_line_id=self.fiscal_operation_line_id,
                ncm=self.ncm_id,
                nbs=self.nbs_id,
                nbm=self.nbm_id,
                cest=self.cest_id,
                discount_value=self.discount_value,
                insurance_value=self.insurance_value,
                other_value=self.other_value,
                freight_value=self.freight_value,
                fiscal_price=self.fiscal_price,
                fiscal_quantity=self.fiscal_quantity,
                uot_id=self.uot_id,
                icmssn_range=self.icmssn_range_id,
                icms_origin=self.icms_origin,
                ind_final=self.ind_final,
                icms_relief_value=self.icms_relief_value,
            ),
        )._get_price_total_and_subtotal(
            price_unit=price_unit or self.price_unit,
            quantity=quantity or self.quantity,
            discount=discount or self.discount,
            currency=currency or self.currency_id,
            product=product or self.product_id,
            partner=partner or self.partner_id,
            taxes=taxes or self.tax_ids,
            move_type=move_type or self.move_id.move_type,
        )

    @api.model
    def _get_price_total_and_subtotal_model(
        self,
        price_unit,
        quantity,
        discount,
        currency,
        product,
        partner,
        taxes,
        move_type,
    ):
        """This method is used to compute 'price_total' & 'price_subtotal'.
        :param price_unit:  The current price unit.
        :param quantity:    The current quantity.
        :param discount:    The current discount.
        :param currency:    The line's currency.
        :param product:     The line's product.
        :param partner:     The line's partner.
        :param taxes:       The applied taxes.
        :param move_type:   The type of the move.
        :return:            A dictionary containing 'price_subtotal' & 'price_total'.
        """
        result = super()._get_price_total_and_subtotal_model(
            price_unit, quantity, discount, currency, product, partner, taxes, move_type
        )

        # Compute 'price_subtotal'.
        line_discount_price_unit = price_unit * (1 - (discount / 100.0))

        insurance_value = self.env.context.get("insurance_value", 0)
        other_value = self.env.context.get("other_value", 0)
        freight_value = self.env.context.get("other_value", 0)
        ii_customhouse_charges = self.env.context.get("ii_customhouse_charges", 0)
        icms_relief_value = self.env.context.get("icms_relief_value", 0)

        # Compute 'price_total'.
        if taxes:
            force_sign = (
                -1 if move_type in ("out_invoice", "in_refund", "out_receipt") else 1
            )
            taxes_res = taxes._origin.with_context(force_sign=force_sign).compute_all(
                line_discount_price_unit,
                currency=currency,
                quantity=quantity,
                product=self.env.context.get("product_id"),
                partner=self.env.context.get("partner_id"),
                is_refund=move_type in ("out_refund", "in_refund"),
                handle_price_include=True,  # FIXME
                fiscal_taxes=self.env.context.get("fiscal_tax_ids"),
                operation_line=self.env.context.get("fiscal_operation_line_id"),
                cfop=self.cfop_id or None,
                ncm=self.env.context.get("ncm_id"),
                nbs=self.env.context.get("nbs_id"),
                nbm=self.env.context.get("nbm_id"),
                cest=self.env.context.get("cest_id"),
                discount_value=self.env.context.get("discount_value"),
                insurance_value=insurance_value,
                other_value=other_value,
                ii_customhouse_charges=ii_customhouse_charges,
                freight_value=freight_value,
                fiscal_price=self.env.context.get("fiscal_price"),
                fiscal_quantity=self.env.context.get("fiscal_quantity"),
                uot_id=self.env.context.get("uot_id"),
                icmssn_range=self.env.context.get("icmssn_range"),
                icms_origin=self.env.context.get("icms_origin"),
                ind_final=self.env.context.get("ind_final"),
            )

            result["price_subtotal"] = taxes_res["total_excluded"]
            result["price_total"] = taxes_res["total_included"]

        result["price_total"] = (
            result["price_total"]
            + insurance_value
            + other_value
            + freight_value
            - icms_relief_value
        )

        return result

    @api.onchange("fiscal_document_line_id")
    def _onchange_fiscal_document_line_id(self):
        if self.fiscal_document_line_id:
            for field in self._shadowed_fields():
                value = getattr(self.fiscal_document_line_id, field)
                if isinstance(value, tuple):  # m2o
                    setattr(self, field, value[0])
                else:
                    setattr(self, field, value)
            # override the default product uom (set by the onchange):
            self.product_uom_id = self.fiscal_document_line_id.uom_id.id

    @api.onchange("fiscal_tax_ids")
    def _onchange_fiscal_tax_ids(self):
        """Ao alterar o campo fiscal_tax_ids que contém os impostos fiscais,
        são atualizados os impostos contábeis relacionados"""
        result = super()._onchange_fiscal_tax_ids()

        # Atualiza os impostos contábeis relacionados aos impostos fiscais
        user_type = "sale"
        if self.move_id.move_type in ("in_invoice", "in_refund"):
            user_type = "purchase"

        self.tax_ids = self.fiscal_tax_ids.account_taxes(
            user_type=user_type, fiscal_operation=self.fiscal_operation_id
        )

        return result

    @api.onchange(
        "amount_currency",
        "currency_id",
        "debit",
        "credit",
        "tax_ids",
        "fiscal_tax_ids",
        "account_id",
        "price_unit",
        "quantity",
        "fiscal_quantity",
        "fiscal_price",
    )
    def _onchange_mark_recompute_taxes(self):
        """Recompute the dynamic onchange based on taxes.
        If the edited line is a tax line, don't recompute anything as the
        user must be able to set a custom value.
        """
        return super()._onchange_mark_recompute_taxes()

    @api.model
    def _get_fields_onchange_subtotal_model(
        self, price_subtotal, move_type, currency, company, date
    ):
        if company.country_id.code != "BR":
            return super()._get_fields_onchange_subtotal_model(
                price_subtotal=price_subtotal,
                move_type=move_type,
                currency=currency,
                company=company,
                date=date,
            )
        # In l10n_br, the calc of these fields is done in the
        # _get_amount_credit_debit method, as the calculation method
        # is completely different.
        return {}

    # These fields are already inherited by _inherits, but there is some limitation of
    # the ORM that the values of these fields are zeroed when called by onchange. This
    # limitation directly affects the _get_amount_credit_debit method.
    amount_untaxed = fields.Monetary(compute="_compute_amounts")
    amount_total = fields.Monetary(compute="_compute_amounts")

    @api.onchange(
        "move_id",
        "amount_untaxed",
        "amount_tax_included",
        "amount_tax_not_included",
        "amount_total",
        "currency_id",
        "company_currency_id",
        "company_id",
        "date",
        "quantity",
        "discount",
        "price_unit",
        "tax_ids",
    )
    def _onchange_price_subtotal(self):
        # Overridden to replace the method that calculates the amount_currency, debit
        # and credit. As this method is called manually in some places to guarantee
        # the calculation of the balance, that's why we prefer not to make a
        # completely new onchange, even if the name is not totally consistent with the
        # fields declared in the api.onchange.
        if self.company_id.country_id.code != "BR":
            return super()._onchange_price_subtotal()
        for line in self:
            if not line.move_id.is_invoice(include_receipts=True):
                continue
            line.update(line._get_price_total_and_subtotal())
            line.update(line._get_amount_credit_debit())

    def _get_amount_credit_debit(
        self,
        move_id=None,
        exclude_from_invoice_tab=None,
        amount_tax_included=None,
        amount_tax_not_included=None,
        amount_tax_withholding=None,
        amount_total=None,
        currency_id=None,
        company_id=None,
        date=None,
        cfop_id=None,
    ):
        self.ensure_one()
        # The formatting was a little strange, but I tried to make it as close as
        # possible to the logic adopted by native Odoo.
        # Example: _get_fields_onchange_subtotal
        return self._get_amount_credit_debit_model(
            move_id=self.move_id if move_id is None else move_id,
            exclude_from_invoice_tab=self.exclude_from_invoice_tab
            if exclude_from_invoice_tab is None
            else exclude_from_invoice_tab,
            amount_tax_included=self.amount_tax_included
            if amount_tax_included is None
            else amount_tax_included,
            amount_tax_not_included=self.amount_tax_not_included
            if amount_tax_not_included is None
            else amount_tax_not_included,
            amount_tax_withholding=self.amount_tax_withholding
            if amount_tax_withholding is None
            else amount_tax_withholding,
            amount_total=self.amount_total if amount_total is None else amount_total,
            currency_id=self.currency_id if currency_id is None else currency_id,
            company_id=self.company_id if company_id is None else company_id,
            date=(self.date or fields.Date.context_today(self))
            if date is None
            else date,
            cfop_id=self.cfop_id if cfop_id is None else cfop_id,
        )

    def _get_amount_credit_debit_model(
        self,
        move_id,
        exclude_from_invoice_tab,
        amount_tax_included,
        amount_tax_not_included,
        amount_tax_withholding,
        amount_total,
        currency_id,
        company_id,
        date,
        cfop_id,
    ):
        if exclude_from_invoice_tab:
            return {}
        if move_id.move_type in move_id.get_outbound_types():
            sign = 1
        elif move_id.move_type in move_id.get_inbound_types():
            sign = -1
        else:
            sign = 1
        if cfop_id and not cfop_id.finance_move:
            amount_currency = 0
        else:
            if move_id.fiscal_operation_id.deductible_taxes:
                amount_currency = amount_total + amount_tax_withholding
            else:
                amount_total = amount_total + amount_tax_withholding
                amount_currency = (
                    amount_total
                    - (amount_tax_included - amount_tax_withholding)
                    - amount_tax_not_included
                )

        amount_currency = amount_currency * sign

        balance = currency_id._convert(
            amount_currency,
            company_id.currency_id,
            company_id,
            date,
        )
        return {
            "amount_currency": amount_currency,
            "currency_id": currency_id.id,
            "debit": balance > 0.0 and balance or 0.0,
            "credit": balance < 0.0 and -balance or 0.0,
        }
