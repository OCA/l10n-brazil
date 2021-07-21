# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
# pylint: disable=api-one-deprecated

from odoo import api, fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import TAX_FRAMEWORK  # FISCAL_IN_OUT,

from .account_invoice import INVOICE_TO_OPERATION

# These fields that have the same name in account.invoice.line
# and l10n_br_fiscal.document.line.mixin. So they won't be updated
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


class AccountInvoiceLine(models.Model):
    _name = "account.invoice.line"
    _inherit = [_name, "l10n_br_fiscal.document.line.mixin.methods"]
    _inherits = {"l10n_br_fiscal.document.line": "fiscal_document_line_id"}

    # initial account.invoice.line inherits on fiscal.document.line that are
    # disable with active=False in their fiscal_document_line table.
    # To make these invoice lines still visible, we set active=True
    # in the invoice.line table.
    active = fields.Boolean(
        string="Active",
        default=True,
    )

    # this default should be overwritten to False in a module pretending to
    # create fiscal documents from the invoices. But this default here
    # allows to install the l10n_br_account module without creating issues
    # with the existing Odoo invoice (demo or not).
    fiscal_document_line_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.line",
        string="Fiscal Document Line",
        required=True,
        copy=False,
        ondelete="cascade",
    )

    document_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.type",
        related="invoice_id.document_type_id",
    )

    tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        related="invoice_id.company_id.tax_framework",
        string="Tax Framework",
    )

    cfop_destination = fields.Selection(
        related="cfop_id.destination", string="CFOP Destination"
    )

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        related="invoice_id.partner_id",
        string="Partner",
    )

    partner_company_type = fields.Selection(related="partner_id.company_type")

    fiscal_genre_code = fields.Char(
        related="fiscal_genre_id.code",
        string="Fiscal Product Genre Code",
    )

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

    @api.one
    @api.depends(
        "price_unit",
        "discount",
        "invoice_line_tax_ids",
        "quantity",
        "product_id",
        "invoice_id.partner_id",
        "invoice_id.currency_id",
        "invoice_id.company_id",
        "invoice_id.date_invoice",
        "invoice_id.date",
        "fiscal_tax_ids",
    )
    def _compute_price(self):
        """Compute the amounts of the SO line."""
        super()._compute_price()
        if self.document_type_id:
            # Update taxes fields
            self._update_taxes()
            # Call mixin compute method
            self._compute_amounts()
            # Update record
            self.update(
                {
                    "discount": self.discount_value,
                    "price_subtotal": self.amount_untaxed + self.discount_value,
                    "price_tax": self.amount_tax,
                    "price_total": self.amount_total,
                }
            )

            price_subtotal_signed = self.price_subtotal

            if (
                self.invoice_id.currency_id
                and self.invoice_id.currency_id
                != self.invoice_id.company_id.currency_id
            ):
                currency = self.invoice_id.currency_id
                date = self.invoice_id._get_currency_rate_date()
                price_subtotal_signed = currency._convert(
                    price_subtotal_signed,
                    self.invoice_id.company_id.currency_id,
                    self.company_id or self.env.user.company_id,
                    date or fields.Date.today(),
                )
            sign = self.invoice_id.type in ["in_refund", "out_refund"] and -1 or 1
            self.price_subtotal_signed = price_subtotal_signed * sign

    @api.depends("price_total")
    def _get_price_tax(self):
        for line in self:
            line.price_tax = line.amount_tax

    @api.model
    def _shadowed_fields(self):
        """Returns the list of shadowed fields that are synced
        from the parent."""
        return SHADOWED_FIELDS

    def _prepare_shadowed_fields_dict(self, default=False):
        self.ensure_one()
        vals = self._convert_to_write(self.read(self._shadowed_fields())[0])
        if default:  # in case you want to use new rather than write later
            return {"default_%s" % (k,): vals[k] for k in vals.keys()}
        return vals

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        inv_type = self.env.context.get("type", "out_invoice")
        defaults["fiscal_operation_type"] = INVOICE_TO_OPERATION[inv_type]
        return defaults

    @api.model
    def create(self, values):
        dummy_doc = self.env.user.company_id.fiscal_dummy_id
        fiscal_doc_id = (
            self.env["account.invoice"]
            .browse(values["invoice_id"])
            .fiscal_document_id.id
        )
        if dummy_doc.id == fiscal_doc_id:
            values["fiscal_document_line_id"] = fields.first(dummy_doc.line_ids).id

        values.update(
            self._update_fiscal_quantity(
                values.get("product_id"),
                values.get("price_unit"),
                values.get("quantity"),
                values.get("uom_id"),
                values.get("uot_id"),
            )
        )

        line = super().create(values)
        if dummy_doc.id != fiscal_doc_id:
            shadowed_fiscal_vals = line._prepare_shadowed_fields_dict()
            doc_id = line.invoice_id.fiscal_document_id.id
            shadowed_fiscal_vals["document_id"] = doc_id
            line.fiscal_document_line_id.write(shadowed_fiscal_vals)
        return line

    def write(self, values):
        dummy_doc = self.env.user.company_id.fiscal_dummy_id
        dummy_line = fields.first(dummy_doc.line_ids)
        if values.get("invoice_id"):
            values["document_id"] = (
                self.env["account.invoice"]
                .browse(values["invoice_id"])
                .fiscal_document_id.id
            )
        result = super().write(values)
        for line in self:
            if line.fiscal_document_line_id != dummy_line:
                shadowed_fiscal_vals = line._prepare_shadowed_fields_dict()
                line.fiscal_document_line_id.write(shadowed_fiscal_vals)
        return result

    def unlink(self):
        dummy_doc = self.env.user.company_id.fiscal_dummy_id
        dummy_line = fields.first(dummy_doc.line_ids)
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

    @api.onchange("fiscal_tax_ids")
    def _onchange_fiscal_tax_ids(self):
        super()._onchange_fiscal_tax_ids()
        user_type = "sale"
        if self.invoice_id.type in ("in_invoice", "in_refund"):
            user_type = "purchase"
        self.invoice_line_tax_ids |= self.fiscal_tax_ids.account_taxes(
            user_type=user_type
        )
