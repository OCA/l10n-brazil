# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


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

    @api.depends("product_id")
    def _compute_name(self):
        for line in self:
            if line.product_id:
                line.name = line.product_id.display_name
            else:
                line.name = False

    @api.depends("product_id")
    def _compute_uom_id(self):
        for line in self:
            if line.fiscal_operation_type == "in":
                line.uom_id = line.product_id.uom_id
            else:
                line.uom_id = line.product_id.uom_id

    def __document_comment_vals(self):
        self.ensure_one()
        return {
            "user": self.env.user,
            "ctx": self.env.context,
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
