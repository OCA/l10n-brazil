# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
# pylint: disable=api-one-deprecated

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import TAX_FRAMEWORK

# These fields that have the same name in account.move.line
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
    _name = "account.move.line"
    _inherit = [_name, "l10n_br_fiscal.document.line.mixin.methods"]
    _inherits = {"l10n_br_fiscal.document.line": "fiscal_document_line_id"}

    # initial account.move.line inherits on fiscal.document.line that are
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
        related="move_id.document_type_id",
    )

    tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        related="move_id.company_id.tax_framework",
        string="Tax Framework",
    )

    cfop_destination = fields.Selection(
        related="cfop_id.destination", string="CFOP Destination"
    )

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        related="move_id.partner_id",
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

    wh_move_line_id = fields.Many2one(
        comodel_name="account.move.line",
        string="WH Account Move Line",
        ondelete="restrict",
    )

    @api.depends(
        "price_unit",
        "discount",
        "tax_ids",
        "quantity",
        "product_id",
        "move_id.partner_id",
        "move_id.currency_id",
        "move_id.company_id",
        "move_id.date",
        "move_id.date",
        "fiscal_tax_ids",
    )
    def _compute_price(self):
        """Compute the amounts of the SO line."""
        # TODO FIXME migrate. No such method in Odoo 13+
        super()._compute_price()
        if self.document_type_id:
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
                self.move_id.currency_id
                and self.move_id.currency_id != self.move_id.company_id.currency_id
            ):
                currency = self.move_id.currency_id
                date = self.move_id._get_currency_rate_date()
                price_subtotal_signed = currency._convert(
                    price_subtotal_signed,
                    self.move_id.company_id.currency_id,
                    self.company_id or self.env.company,
                    date or fields.Date.today(),
                )
            sign = self.move_id.type in ["in_refund", "out_refund"] and -1 or 1
            self.price_subtotal_signed = price_subtotal_signed * sign

    @api.depends("price_total")
    def _get_price_tax(self):
        # TODO FIXME migrate. No such method in Odoo 13+
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
    def create(self, values):
        dummy_doc = self.env.company.fiscal_dummy_id
        fiscal_doc_id = (
            self.env["account.move"].browse(values["move_id"]).fiscal_document_id.id
        )
        if dummy_doc.id == fiscal_doc_id or values.get("exclude_from_invoice_tab"):
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
            doc_id = line.move_id.fiscal_document_id.id
            shadowed_fiscal_vals["document_id"] = doc_id
            line.fiscal_document_line_id.write(shadowed_fiscal_vals)

        return line

    def write(self, values):
        dummy_doc = self.env.company.fiscal_dummy_id
        dummy_line = fields.first(dummy_doc.line_ids)
        if values.get("move_id"):
            values["document_id"] = (
                self.env["account.move"].browse(values["move_id"]).fiscal_document_id.id
            )
        result = super().write(values)
        for line in self:
            if line.wh_move_line_id and (
                "quantity" in values or "price_unit" in values
            ):
                raise UserError(
                    _("You can't edit one invoice related a withholding entry")
                )
            if line.fiscal_document_line_id != dummy_line:
                shadowed_fiscal_vals = line._prepare_shadowed_fields_dict()
                line.fiscal_document_line_id.write(shadowed_fiscal_vals)
        return result

    def unlink(self):
        dummy_doc = self.env.company.fiscal_dummy_id
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
        if self.move_id.type in ("in_invoice", "in_refund"):
            user_type = "purchase"
        self.tax_ids |= self.fiscal_tax_ids.account_taxes(user_type=user_type)
