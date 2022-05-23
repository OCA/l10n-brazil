# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
# pylint: disable=api-one-deprecated

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# These fields have the same name in account.move.line
# and l10n_br_fiscal.document.line.mixin. So they wouldn't get updated
# by the _inherits system. An alternative would be changing their name
# in l10n_br_fiscal but that would make the code unreadable and fiscal mixin
# methods would fail to do what we expect from them in the Odoo objects
# where they are injected.
SHADOWED_FIELDS = [
    "name",
    "partner_id",
    "company_id",
    "currency_id",
    "product_id",
    "uom_id",
    "quantity",
    "price_unit",
    "discount_value",
]


class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _inherit = [_name, "l10n_br_fiscal.document.line.mixin.methods"]
    _inherits = {"l10n_br_fiscal.document.line": "fiscal_document_line_id"}

    # some account.move.line records _inherits from an fiscal.document.line that is
    # disabled with active=False (dummy record) in the l10n_br_fiscal_document_line table.
    # To make the invoice lines still visible, we set active=True
    # in the account_move_line table.
    active = fields.Boolean(
        string="Active",
        default=True,
    )

    fiscal_document_line_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.line",
        string="Fiscal Document Line",
        required=True,
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

    fiscal_genre_code = fields.Char(
        related="fiscal_genre_id.code",
        string="Fiscal Product Genre Code",
    )

    fiscal_tax_line_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Originator Fiscal Tax",
        ondelete="restrict",
        store=True,
        compute="_compute_tax_line_id",
        help="Indicates that this journal item is a tax line",
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

    wh_move_line_id = fields.Many2one(
        comodel_name="account.move.line",
        string="WH Account Move Line",
        ondelete="restrict",
    )

    @api.model
    def _shadowed_fields(self):
        """Returns the list of shadowed fields that are synchronized
        from the parent."""
        return SHADOWED_FIELDS

    def _prepare_shadowed_fields_dict(self, default=False):
        self.ensure_one()
        vals = self._convert_to_write(self.read(self._shadowed_fields())[0])
        if default:  # in case you want to use new rather than write later
            return {"default_%s" % (k,): vals[k] for k in vals.keys()}
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        dummy_doc = self.env.company.fiscal_dummy_id
        dummy_line = fields.first(dummy_doc.fiscal_line_ids)
        for values in vals_list:
            fiscal_doc_id = (
                self.env["account.move"].browse(values["move_id"]).fiscal_document_id.id
            )
            if fiscal_doc_id == dummy_doc.id or values.get("exclude_from_invoice_tab"):
                if len(dummy_line) < 1:
                    raise UserError(
                        _(
                            "Document line dummy not found. Please contact "
                            "your system administrator."
                        )
                    )
                values["fiscal_document_line_id"] = dummy_line.id

            values.update(
                self._update_fiscal_quantity(
                    values.get("product_id"),
                    values.get("price_unit"),
                    values.get("quantity"),
                    values.get("uom_id"),
                    values.get("uot_id"),
                )
            )

        lines = super().create(vals_list)
        for line in lines.filtered(lambda l: l.fiscal_document_line_id != dummy_line):
            shadowed_fiscal_vals = line._prepare_shadowed_fields_dict()
            doc_id = line.move_id.fiscal_document_id.id
            shadowed_fiscal_vals["document_id"] = doc_id
            line.fiscal_document_line_id.write(shadowed_fiscal_vals)

        return lines

    def write(self, values):
        dummy_doc = self.env.company.fiscal_dummy_id
        dummy_line = fields.first(dummy_doc.fiscal_line_ids)
        non_dummy = self.filtered(lambda l: l.fiscal_document_line_id != dummy_line)
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
            if line.wh_move_line_id and (
                "quantity" in values or "price_unit" in values
            ):
                raise UserError(
                    _("You cannot edit an invoice related to a withholding entry")
                )
            if line.fiscal_document_line_id != dummy_line:
                shadowed_fiscal_vals = line._prepare_shadowed_fields_dict()
                line.fiscal_document_line_id.write(shadowed_fiscal_vals)
        return result

    def unlink(self):
        dummy_doc = self.env.company.fiscal_dummy_id
        dummy_line = fields.first(dummy_doc.fiscal_line_ids)
        unlink_fiscal_lines = self.env["l10n_br_fiscal.document.line"]
        for inv_line in self:
            if not inv_line.exists():
                continue
            if inv_line.fiscal_document_line_id.id != dummy_line.id:
                unlink_fiscal_lines |= inv_line.fiscal_document_line_id
        result = super().unlink()
        unlink_fiscal_lines.unlink()
        self.clear_caches()
        return result

    def _get_fields_onchange_balance(
        self,
        quantity=None,
        discount=None,
        amount_currency=None,
        move_type=None,
        currency=None,
        taxes=None,
        price_subtotal=None,
        force_computation=False,
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
                uot=self.uot_id,
                icmssn_range=self.icmssn_range_id,
                icms_origin=self.icms_origin,
            ),
        )._get_fields_onchange_balance_model(
            quantity=quantity or self.quantity,
            discount=discount or self.discount,
            amount_currency=amount_currency or self.amount_currency,
            move_type=move_type or self.move_id.move_type,
            currency=currency or self.currency_id or self.move_id.currency_id,
            taxes=taxes or self.tax_ids,
            price_subtotal=price_subtotal or self.price_subtotal,
            force_computation=force_computation,
        )

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
        """This method is used to recompute the values of 'quantity',
        'discount', 'price_unit' due to a change made
        in some accounting fields such as 'balance'.
        This method is a bit complex as we need to handle some special cases.
        For example, setting a positive balance with a 100% discount.
        :param quantity:        The current quantity.
        :param discount:        The current discount.
        :param amount_currency: The new balance in line's currency.
        :param move_type:       The type of the move.
        :param currency:        The currency.
        :param taxes:           The applied taxes.
        :param price_subtotal:  The price_subtotal.
        :return:                A dictionary containing 'quantity',
                                'discount', 'price_unit'.
        """

        if move_type in self.move_id.get_outbound_types():
            sign = 1
        elif move_type in self.move_id.get_inbound_types():
            sign = -1
        else:
            sign = 1
        amount_currency *= sign

        # Avoid rounding issue when dealing with price included taxes.
        # For example, when the price_unit is 2300.0 and
        # a 5.5% price included tax is applied on it, a balance
        # of 2300.0 / 1.055 = 2180.094 ~ 2180.09 is computed.
        # However, when triggering the inverse, 2180.09 + (2180.09 * 0.055)
        # = 2180.09 + 119.90 = 2299.99 is computed.
        # To avoid that, set the price_subtotal at the balance if the
        # difference between them looks like a rounding issue.
        if not force_computation and currency.is_zero(amount_currency - price_subtotal):
            return {}

        taxes = taxes.flatten_taxes_hierarchy()
        if taxes and any(tax.price_include for tax in taxes):
            force_sign = (
                -1 if move_type in ("out_invoice", "in_refund", "out_receipt") else 1
            )
            taxes_res = taxes._origin.with_context(force_sign=force_sign).compute_all(
                amount_currency,
                currency=currency,
                quantity=quantity,
                partner=self.env.context.get("partner_id"),
                product=self.env.context.get("product_id"),
                is_refund=move_type in ("out_refund", "in_refund"),
                handle_price_include=False,  # FIXME
                fiscal_taxes=self.env.context.get("fiscal_tax_ids"),
                operation_line=self.env.context.get("fiscal_operation_line_id"),
                ncm=self.env.context.get("ncm_id"),
                nbs=self.env.context.get("nbs_id"),
                nbm=self.env.context.get("nbm_id"),
                cest=self.env.context.get("cest_id"),
                discount_value=self.env.context.get("discount_value"),
                insurance_value=self.env.context.get("insurance_value"),
                other_value=self.env.context.get("other_value"),
                freight_value=self.env.context.get("freight_value"),
                fiscal_price=self.env.context.get("fiscal_price"),
                fiscal_quantity=self.env.context.get("fiscal_quantity"),
                uot=self.env.context.get("uot_id"),
                icmssn_range=self.env.context.get("icmssn_range"),
                icms_origin=self.env.context.get("icms_origin"),
            )

            for tax_res in taxes_res["taxes"]:

                if tax_res.get("price_include"):
                    amount_currency += tax_res["amount"]

        discount_factor = 1 - (discount / 100.0)
        if amount_currency and discount_factor:
            # discount != 100%
            vals = {
                "quantity": quantity or 1.0,
                "price_unit": amount_currency / discount_factor / (quantity or 1.0),
            }
        elif amount_currency and not discount_factor:
            # discount == 100%
            vals = {
                "quantity": quantity or 1.0,
                "discount": 0.0,
                "price_unit": amount_currency / (quantity or 1.0),
            }
        elif not discount_factor:
            # balance of line is 0, but discount  == 100% so we display the normal unit_price
            vals = {}
        else:
            # balance is 0, so unit price is 0 as well
            vals = {"price_unit": 0.0}
        return vals

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
                uot=self.uot_id,
                icmssn_range=self.icmssn_range_id,
                icms_origin=self.icms_origin,
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
                ncm=self.env.context.get("ncm_id"),
                nbs=self.env.context.get("nbs_id"),
                nbm=self.env.context.get("nbm_id"),
                cest=self.env.context.get("cest_id"),
                discount_value=self.env.context.get("discount_value"),
                insurance_value=self.env.context.get("insurance_value"),
                other_value=self.env.context.get("other_value"),
                freight_value=self.env.context.get("freight_value"),
                fiscal_price=self.env.context.get("fiscal_price"),
                fiscal_quantity=self.env.context.get("fiscal_quantity"),
                uot=self.env.context.get("uot_id"),
                icmssn_range=self.env.context.get("icmssn_range"),
                icms_origin=self.env.context.get("icms_origin"),
            )

            result["price_subtotal"] = taxes_res["total_excluded"]
            result["price_total"] = taxes_res["total_included"]

            fol = self.env.context.get("fiscal_operation_line_id")
            if fol and not fol.fiscal_operation_id.deductible_taxes:
                result["price_subtotal"] = (
                    taxes_res["total_excluded"] - taxes_res["amount_tax_included"]
                )
                result["price_total"] = (
                    taxes_res["total_included"] - taxes_res["amount_tax_included"]
                )

        return result

    @api.onchange("fiscal_tax_ids")
    def _onchange_fiscal_tax_ids(self):
        """Ao alterar o campo fiscal_tax_ids que contém os impostos fiscais,
        são atualizados os impostos contábeis relacionados"""
        super()._onchange_fiscal_tax_ids()
        user_type = "sale"

        # Atualiza os impostos contábeis relacionados aos impostos fiscais
        if self.move_id.move_type in ("in_invoice", "in_refund"):
            user_type = "purchase"
        self.tax_ids |= self.fiscal_tax_ids.account_taxes(user_type=user_type)

        # Caso a operação fiscal esteja definida para usar o impostos
        # dedutíveis os impostos contáveis deduvíveis são adicionados na linha
        # da movimentação/fatura.
        if self.fiscal_operation_id and self.fiscal_operation_id.deductible_taxes:
            self.tax_ids |= self.fiscal_tax_ids.account_taxes(
                user_type=user_type, deductible=True
            )

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
