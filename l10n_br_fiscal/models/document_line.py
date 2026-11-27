# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.tools import float_compare

from ..tools import cfop_geography_warning

# The review of an imported line converts quantity and price on purpose, and the
# total declared in the file must survive it.
IMPORT_REVIEW_CONTEXT_KEY = "import_review_apply"


class DocumentLine(models.Model):
    """
    Represents a line item within a Brazilian fiscal document.

    This model defines the core structure of a fiscal document line,
    primarily linking it to its parent document (`l10n_br_fiscal.document`)
    and holding essential line-specific data like quantity and a
    descriptive name.

    The vast majority of detailed fiscal fields (e.g., product, NCM,
    CFOP, various tax bases and values) and their complex computation
    logic are inherited from `l10n_br_fiscal.document.line.mixin`.
    This delegation ensures code reusability and keeps this model
    focused on its direct relationships and core line properties.
    """

    _name = "l10n_br_fiscal.document.line"
    _inherit = "l10n_br_fiscal.document.line.mixin"
    _description = "Fiscal Document Line"

    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Document",
        ondelete="cascade",
    )

    name = fields.Char(
        compute="_compute_name",
        store=True,
        precompute=True,
        readonly=False,
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        related="document_id.company_id",
        store=True,
        precompute=True,
        string="Company",
    )

    tax_framework = fields.Selection(
        related="company_id.tax_framework",
    )

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        compute="_compute_partner_id",
        store=True,
        precompute=True,
        readonly=False,
    )

    # Do not depend on `document_id.partner_id`, the inverse is taking care of that
    def _compute_partner_id(self):
        for line in self:
            line.partner_id = line.document_id.partner_id

    uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="UOM",
        compute="_compute_uom_id",
        store=True,
        readonly=False,
        precompute=True,
    )

    price_unit = fields.Float(
        digits="Product Price",
        compute="_compute_price_unit_fiscal",
        store=True,
        precompute=True,
        readonly=False,
    )

    quantity = fields.Float(default=1.0)

    # Usado para tornar Somente Leitura os campos dos custos
    # de entrega quando a definição for por Total
    delivery_costs = fields.Selection(
        related="company_id.delivery_costs",
    )

    force_compute_delivery_costs_by_total = fields.Boolean(
        related="document_id.force_compute_delivery_costs_by_total"
    )

    edoc_purpose = fields.Selection(
        related="document_id.edoc_purpose",
    )

    additional_data = fields.Text()

    # Values as the counterparty declared them in an imported fiscal file. The
    # document is created faithful to the file, and the review of each line
    # converts it to the internal nomenclature without losing what was declared.
    partner_uom_code = fields.Char(
        string="Unit Declared by Partner",
        readonly=True,
        copy=False,
        help="Unit of measure as declared by the counterparty in the imported "
        "document.",
    )

    partner_quantity = fields.Float(
        string="Quantity Declared by Partner",
        digits="Product Unit of Measure",
        readonly=True,
        copy=False,
        help="Quantity as declared by the counterparty, in its own unit.",
    )

    partner_price_unit = fields.Float(
        string="Unit Price Declared by Partner",
        digits="Product Price",
        readonly=True,
        copy=False,
        help="Unit price as declared by the counterparty, in its own unit.",
    )

    cfop_warning = fields.Char(
        string="CFOP Alert",
        compute="_compute_cfop_warning",
        help="Warns when the CFOP declared by the counterparty contradicts the "
        "geography of the issuer and of the company, to spot a supplier mistake "
        "before it reaches the fiscal books.",
    )

    def write(self, vals):
        edited = self.browse()
        if (
            "partner_price_gross" not in vals
            and {"quantity", "price_unit"} & vals.keys()
            and not self.env.context.get(IMPORT_REVIEW_CONTEXT_KEY)
        ):
            # A quantity or a price changed by a person gives the total back to
            # the calculation; writing the same values back changes nothing.
            edited = self.filtered(
                lambda line: line.partner_price_gross
                and any(
                    name in vals
                    and float_compare(vals[name], line[name], precision_digits=8)
                    for name in ("quantity", "price_unit")
                )
            )
        if edited:
            super(DocumentLine, edited).write(dict(vals, partner_price_gross=0.0))
        result = super(DocumentLine, self - edited).write(vals)
        if vals.get("cfop_id") and "cfop_manual" not in vals:
            # The automatic remap goes through the compute, which never calls
            # write: a CFOP written on an imported line is a decision of a person.
            self.filtered(
                lambda line: line._is_imported() and not line.cfop_manual
            ).write({"cfop_manual": True})
        return result

    @api.depends(
        "partner_cfop_id",
        "document_id.partner_id.state_id",
        "document_id.partner_id.country_id",
    )
    def _compute_cfop_warning(self):
        for line in self:
            line.cfop_warning = (
                cfop_geography_warning(
                    line.partner_cfop_id.code,
                    line.document_id.partner_id,
                    line.company_id,
                )
                if line.document_id.fiscal_operation_type == "in"
                else False
            )

    def _get_partner_product_code(self):
        """Code of the product in the catalog of the counterparty."""
        self.ensure_one()
        return False

    def _get_partner_product_name(self):
        """Name of the product in the catalog of the counterparty."""
        self.ensure_one()
        return False

    @api.depends("fiscal_operation_id", "partner_id", "product_id")
    def _compute_fiscal_operation_line_id(self):
        """An imported line keeps the operation line it has while it belongs to the
        operation of the line: the product that the review gives it must not take
        the operation line away, or the line stops adding to the financial total of
        the document (and the document has nothing to pay)."""
        kept = {
            line: line.fiscal_operation_line_id
            for line in self
            if line._is_imported()
            and line.fiscal_operation_line_id
            and line.fiscal_operation_line_id.fiscal_operation_id
            == line.fiscal_operation_id
        }
        result = super()._compute_fiscal_operation_line_id()
        for line, operation_line in kept.items():
            line.fiscal_operation_line_id = operation_line
        return result

    @api.depends("product_id")
    def _compute_name(self):
        for line in self:
            if line._is_imported() and line.name:
                # the description declared in the file
                line.name = line.name
                continue
            if line.product_id:
                line.name = line.product_id.display_name
            else:
                line.name = False

    @api.depends("product_id")
    def _compute_uom_id(self):
        for line in self:
            if line._is_imported() and (line.uom_id or line.partner_uom_code):
                # the unit declared in the file, even when it matched no unit: the
                # product does not give a unit the file did not bring, and the
                # review applies the internal one
                line.uom_id = line.uom_id
                continue
            if line.fiscal_operation_type == "in":
                line.uom_id = line.product_id.uom_po_id
            else:
                line.uom_id = line.product_id.uom_id

    def __document_comment_vals(self):
        self.ensure_one()
        return {
            "user": self.env.user,
            "ctx": self._context,
            "doc": self.document_id if hasattr(self, "document_id") else None,
            "item": self,
        }

    def _document_comment(self):
        for line in self:
            line.additional_data = line.comment_ids.compute_message(
                line.__document_comment_vals(), line.manual_additional_data
            )

    @api.model
    def _add_imported_ibscbs_vals(self, ibscbs, vals):
        """Merge into ``vals`` the IBS/CBS values of an imported IBSCBS
        binding node (NFe and CTe share the same DFe schema for it).

        Returns the list of matched fiscal tax ids so each caller can
        link them into ``fiscal_tax_ids`` with its own convention (the
        NFe import framework expects raw ids, the CTe one expects
        Command tuples).
        """
        tax_ids = []
        if not (ibscbs and ibscbs.gIBSCBS):
            return tax_ids

        gibscbs = ibscbs.gIBSCBS
        base = float(gibscbs.vBC) if gibscbs.vBC else 0.0

        ibs_percent = ibs_value = 0.0
        if gibscbs.gIBSUF:
            ibs_percent = float(gibscbs.gIBSUF.pIBSUF) if gibscbs.gIBSUF.pIBSUF else 0.0
            ibs_value = float(gibscbs.gIBSUF.vIBSUF) if gibscbs.gIBSUF.vIBSUF else 0.0
        cbs_percent = cbs_value = 0.0
        if gibscbs.gCBS:
            cbs_percent = float(gibscbs.gCBS.pCBS) if gibscbs.gCBS.pCBS else 0.0
            cbs_value = float(gibscbs.gCBS.vCBS) if gibscbs.gCBS.vCBS else 0.0

        cst_code = ibscbs.CST if ibscbs.CST else "000"
        cst_ibs = self.env.ref(
            f"l10n_br_fiscal.cst_ibs_{cst_code}", raise_if_not_found=False
        )
        if cst_ibs:
            vals["ibs_cst_id"] = cst_ibs.id
        cst_cbs = self.env.ref(
            f"l10n_br_fiscal.cst_cbs_{cst_code}", raise_if_not_found=False
        )
        if cst_cbs:
            vals["cbs_cst_id"] = cst_cbs.id

        if ibscbs.cClassTrib:
            tax_classification = self.env["l10n_br_fiscal.tax.classification"].search(
                [("code", "=", ibscbs.cClassTrib)], limit=1
            )
            if tax_classification:
                vals["tax_classification_id"] = tax_classification.id

        vals.update(
            ibs_base=base,
            ibs_percent=ibs_percent,
            ibs_value=ibs_value,
            cbs_base=base,
            cbs_percent=cbs_percent,
            cbs_value=cbs_value,
        )

        ibs_tax = self.env["l10n_br_fiscal.tax"].search(
            [
                ("tax_group_id", "=", self.env.ref("l10n_br_fiscal.tax_group_ibs").id),
                ("percent_amount", "=", ibs_percent),
            ],
            limit=1,
        )
        if ibs_tax:
            vals["ibs_tax_id"] = ibs_tax.id
            tax_ids.append(ibs_tax.id)
        cbs_tax = self.env["l10n_br_fiscal.tax"].search(
            [
                ("tax_group_id", "=", self.env.ref("l10n_br_fiscal.tax_group_cbs").id),
                ("percent_amount", "=", cbs_percent),
            ],
            limit=1,
        )
        if cbs_tax:
            vals["cbs_tax_id"] = cbs_tax.id
            tax_ids.append(cbs_tax.id)
        return tax_ids
