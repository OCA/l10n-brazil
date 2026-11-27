# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# pylint: disable=consider-merging-classes-inherited

from odoo import _, fields, models
from odoo.exceptions import AccessError, UserError

from odoo.addons.l10n_br_fiscal.models.document_line import IMPORT_REVIEW_CONTEXT_KEY


class DocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    # Review of the lines of an imported document: the line is created faithful to
    # the file, and each one is reviewed (matched to a product, unit and factor
    # chosen) while the supplier values stay in the partner_* fields.
    import_state = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("matched", "Matched"),
            ("resolved", "Resolved"),
        ],
        copy=False,
        index=True,
        help="Review state of a line imported from a fiscal document file. "
        "Pending: no product was resolved, or the unit declared by the supplier "
        "was neither matched nor chosen. Matched: a suggestion waits for the "
        "confirmation of a person. Resolved: the review was applied. Empty on a "
        "line that was not imported.",
    )

    import_uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="Import UoM",
        copy=False,
        help="Unit of the company that is equivalent to the unit of the supplier.",
    )

    import_uom_factor = fields.Float(
        string="Import UoM Factor",
        # no default: the column of a field with a default is filled for every line
        # of every document when the module is installed; an empty factor is 1.0
        copy=False,
        help="How many units of the company make one unit of the supplier (25 for "
        "a bag of 25 kg received in KG).",
    )

    import_supplierinfo_id = fields.Many2one(
        comodel_name="product.supplierinfo",
        string="Import Supplier Info",
        copy=False,
    )

    def _import_unit_unconfirmed(self):
        """The unit declared by the supplier was neither matched nor chosen."""
        self.ensure_one()
        if not self.partner_uom_code or self.import_uom_id:
            return False
        declared = self.env["uom.uom"]._match_by_fiscal_code(self.partner_uom_code)
        return not self.uom_id or declared != self.uom_id

    def write(self, vals):
        """Choosing the product of a line that is under review is for the fiscal
        profile. The screens check it, but the access list of the line can be open
        to other users (l10n_br_account gives it to every internal user), so the
        check is also here: whoever writes the line directly meets the same rule."""
        if (
            "product_id" in vals
            and not self.env.su
            and not self.env.user.has_group("l10n_br_fiscal.group_user")
            and any(
                line._is_imported() and line.import_state in ("pending", "matched")
                for line in self.sudo()
            )
        ):
            raise AccessError(
                _(
                    "Choosing the product of a line under review is for the fiscal "
                    "profile. Ask a fiscal user to resolve the line."
                )
            )
        return super().write(vals)

    def action_resolve_line(self):
        for line in self:
            if not line.product_id:
                raise UserError(
                    _("Set the product of the line %s before resolving it.")
                    % (line.name or line.id)
                )
            line._apply_import_depara()
        # The button sits in the dialog of the line: the form of the document keeps
        # the values it read before (the taxes of the product, for one), so it is
        # read again.
        return {"type": "ir.actions.client", "tag": "reload"}

    def _apply_import_depara(
        self, product=None, uom=None, factor=None, fiscal_operation=None
    ):
        """Apply the review of an imported line.

        The values declared by the supplier are kept in the partner_* fields, the
        quantity is multiplied by the factor and the unit price divided by it, so
        that the total of the line does not change, and what the line learned
        goes to the supplier info of the product. The line is resolved only when
        its unit is confirmed.
        """
        self.ensure_one()
        if not self._is_imported():
            raise UserError(
                _("The review can only be applied on the line of an imported document.")
            )
        line = self.with_context(**{IMPORT_REVIEW_CONTEXT_KEY: True})
        product = product or line.product_id
        uom = uom or line.import_uom_id
        factor = factor or line.import_uom_factor or 1.0
        fiscal_operation = fiscal_operation or line.fiscal_operation_id
        if not (line.partner_quantity or line.partner_price_unit):
            # Taken once, before the first conversion: a line already reviewed
            # holds the converted values and would compound the factor.
            line.write(
                {
                    "partner_quantity": line.quantity,
                    "partner_price_unit": line.price_unit,
                }
            )
        # A line whose unit matched nothing has no snapshot to convert from
        declared_quantity = line.partner_quantity or line.quantity
        declared_price_unit = line.partner_price_unit or line.price_unit
        vals = {
            "import_uom_factor": factor,
            "quantity": declared_quantity * factor,
            "price_unit": declared_price_unit / factor,
        }
        if product:
            vals["product_id"] = product.id
        if uom:
            vals["import_uom_id"] = uom.id
            vals["uom_id"] = uom.id
        if fiscal_operation:
            vals["fiscal_operation_id"] = fiscal_operation.id
        line.write(vals)
        line.import_state = "pending" if line._import_unit_unconfirmed() else "resolved"
        if product:
            line._find_or_create_supplierinfo()
        return True

    def _suggest_fiscal_operation_in(self):
        """Operation that receives the CFOP the issuer declared on the line."""
        self.ensure_one()
        return (
            self.env["l10n_br_fiscal.operation.line"]
            ._find_by_issuer_cfop(
                self.partner_cfop_id, self.document_id.partner_operation_name, "in"
            )
            .fiscal_operation_id
        )

    def _get_supplierinfo_unit(self, supplierinfo):
        """Unit of the supplier and factor learned on the supplier info."""
        self.ensure_one()
        return self.env["uom.uom"], 1.0

    def _prepare_supplierinfo_vals(self):
        self.ensure_one()
        return {
            "product_id": self.product_id.id,
            "product_name": self._get_partner_product_name() or self.name,
            "product_code": self._get_partner_product_code(),
        }

    def _find_or_create_supplierinfo(self):
        """Learn the mapping of the supplier code to the product (the de-para).

        It is a by-product of the review: the fiscal user has no right on
        purchases, and the sudo of the 16.0 keeps the user, so the author of the
        record is who reviewed the line.
        """
        for line in self.sudo():
            partner = line.document_id.partner_id
            if not line.product_id or not partner:
                continue
            supplierinfo_model = line.env["product.supplierinfo"].with_company(
                line.company_id
            )
            supplierinfo = line.import_supplierinfo_id
            if not supplierinfo:
                # The de-para already learned for this partner, code and product,
                # possibly by an earlier document: a new record on every import
                # would pile up sellers on the product. A seller entered by hand
                # sits on the template, the one created here on the variant.
                supplierinfo = supplierinfo_model.search(
                    [
                        # the registry of another company is not this one's mapping
                        ("company_id", "in", [False, line.company_id.id]),
                        ("partner_id", "=", partner.id),
                        ("product_code", "=", line._get_partner_product_code()),
                        "|",
                        ("product_id", "=", line.product_id.id),
                        ("product_tmpl_id", "=", line.product_id.product_tmpl_id.id),
                    ],
                    limit=1,
                )
            if supplierinfo:
                # What is learned is the code and the name of the supplier; neither the
                # price, which purchasing negotiates, nor the product of a registry
                # that sits on the template (a variant would take it from the others).
                vals = line._prepare_supplierinfo_vals()
                vals.pop("product_id")
                supplierinfo.write(vals)
                line.import_supplierinfo_id = supplierinfo
            else:
                vals = line._prepare_supplierinfo_vals()
                vals["partner_id"] = partner.id
                line.import_supplierinfo_id = supplierinfo_model.create(vals)
                line.product_id.product_tmpl_id.seller_ids = [
                    fields.Command.link(line.import_supplierinfo_id.id)
                ]
