# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..tools import cfop_geography_warning


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

    # Review of lines imported from a fiscal file (draft-first import flow).
    # The document is materialized faithfully from the file and each line is
    # then reviewed: the de-para (supplier nomenclature -> company fiscal
    # settings) is applied on the persisted line, keeping the supplier data
    # as a snapshot for bookkeeping and audit.
    import_state = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("matched", "Matched"),
            ("resolved", "Resolved"),
        ],
        copy=False,
        index=True,
        help="Review state of a line imported from a fiscal document file. "
        "Pending: no internal product resolved yet. Matched: an automatic "
        "suggestion needs confirmation. Resolved: the mapping was applied. "
        "Empty on lines that were not imported.",
    )

    import_uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="Import UoM",
        copy=False,
        help="Internal UoM equivalent to the supplier unit of the imported " "line.",
    )

    import_uom_factor = fields.Float(
        string="Import UoM Factor",
        default=1.0,
        copy=False,
        help="Conversion factor between the supplier unit and the internal "
        "UoM (e.g. 25 for a 25kg bag received in KG).",
    )

    import_supplierinfo_id = fields.Many2one(
        comodel_name="product.supplierinfo",
        string="Import Supplier Info",
        copy=False,
    )

    # Snapshot of the supplier values, taken when the de-para converts the
    # line to the internal nomenclature. partner_cfop_id (mixin) is the same
    # pattern for the CFOP.
    partner_uom_code = fields.Char(
        readonly=True,
        copy=False,
        help="Unit of measure as declared by the counterparty in the "
        "imported document.",
    )

    partner_quantity = fields.Float(
        digits="Product Unit of Measure",
        readonly=True,
        copy=False,
        help="Quantity as declared by the counterparty, in its own unit.",
    )

    partner_price_unit = fields.Float(
        digits="Product Price",
        readonly=True,
        copy=False,
        help="Unit price as declared by the counterparty, in its own unit.",
    )

    cfop_warning = fields.Char(
        compute="_compute_cfop_warning",
        string="CFOP Alert",
        help="Warns when the CFOP declared by the counterparty is "
        "inconsistent with the actual issuer/company geography. Useful to "
        "spot supplier mistakes before they pollute the SPED books.",
    )

    def write(self, vals):
        result = super().write(vals)
        if vals.get("cfop_id") and "cfop_manual" not in vals:
            # Writing the CFOP of an imported line is always a human decision
            # (the automatic remap goes through the compute, which never
            # calls write): flag it so a later recompute keeps it.
            self.filtered(
                lambda line: line._is_imported() and not line.cfop_manual
            ).write({"cfop_manual": True})
        return result

    @api.depends("product_id")
    def _compute_name(self):
        for line in self:
            if line._is_imported() and line.name:
                # Preserve the description imported from the fiscal file.
                line.name = line.name
                continue
            if line.product_id:
                line.name = line.product_id.display_name
            else:
                line.name = False

    @api.depends("product_id")
    def _compute_uom_id(self):
        for line in self:
            if line._is_imported() and line.uom_id:
                # Preserve the unit imported from the fiscal file; the
                # internal unit is applied via _apply_import_depara().
                line.uom_id = line.uom_id
                continue
            if line.fiscal_operation_type == "in":
                line.uom_id = line.product_id.uom_po_id
            else:
                line.uom_id = line.product_id.uom_id

    @api.depends(
        "partner_cfop_id",
        "document_id.partner_id.state_id",
        "document_id.partner_id.country_id",
    )
    def _compute_cfop_warning(self):
        for line in self:
            line.cfop_warning = line._get_cfop_warning()

    def _get_cfop_warning(self):
        """Compare the declared CFOP scope with the real issuer/company
        geography (see ``tools.cfop_geography_warning``)."""
        self.ensure_one()
        if self.document_id.fiscal_operation_type != "in":
            return False
        return cfop_geography_warning(
            self.partner_cfop_id.code,
            self.document_id.partner_id,
            self.company_id,
        )

    def action_resolve_line(self):
        for line in self:
            if not line.product_id:
                raise UserError(
                    _("Set the internal product before resolving the line %s.")
                    % (line.name or line.id)
                )
            line._apply_import_depara()

    def action_open_resolve_wizard(self):
        """Open the focused resolution dialog of the line: one place with the
        supplier data on one side, the internal de-para on the other, a live
        preview of the conversion and a single primary action. It replaces
        hunting for fields across the line form and the tree buttons."""
        self.ensure_one()
        suggested = self._suggest_fiscal_operation_in()
        wizard = self.env["l10n_br_fiscal.document.line.resolve.wizard"].create(
            {
                "line_id": self.id,
                "mode": "link" if self.product_id else "create",
                "partner_name": self._get_partner_product_name() or self.name,
                "partner_product_code": self._get_partner_product_code(),
                "partner_uom_code": self.partner_uom_code or self.uom_id.name,
                "partner_quantity": self.partner_quantity or self.quantity,
                "partner_price_unit": self.partner_price_unit or self.price_unit,
                "partner_ncm_code": self._get_partner_product_ncm(),
                "partner_cfop_id": self.partner_cfop_id.id,
                "cfop_warning": self.cfop_warning,
                "product_id": self.product_id.id,
                "import_uom_id": (self.import_uom_id or self.uom_id).id,
                "import_uom_factor": self.import_uom_factor or 1.0,
                "fiscal_operation_id": (self.fiscal_operation_id or suggested).id,
                "fiscal_operation_suggested": bool(
                    suggested and not self.fiscal_operation_id
                ),
                "currency_id": self.currency_id.id,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Resolve Imported Line"),
            "res_model": "l10n_br_fiscal.document.line.resolve.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    def _open_next_pending_resolve_wizard(self):
        """After resolving, jump straight to the next pending line of the same
        document, so a reviewer works a run of lines without going back to the
        tree between each. Scoped to THIS document (never a global search)."""
        self.ensure_one()
        pending = self.document_id.fiscal_line_ids.filtered(
            lambda line: line.import_state == "pending" and line.id != self.id
        ).sorted("id")
        if not pending:
            return {"type": "ir.actions.act_window_close"}
        return pending[0].action_open_resolve_wizard()

    def _apply_import_depara(
        self, product=None, uom=None, factor=None, fiscal_operation=None
    ):
        """Apply the reviewed de-para on a line imported from a fiscal file.

        This is the single write path of the de-para: it snapshots the
        supplier values (unit, quantity, unit price), converts the line to
        the internal nomenclature preserving the line total (quantity is
        multiplied by the factor, the unit price divided by it), applies the
        fiscal operation of the line and persists the supplier info
        learning. The original file stays untouched as an attachment.
        """
        self.ensure_one()
        if not self._is_imported():
            raise UserError(
                _("The mapping can only be applied on imported document lines.")
            )
        product = product or self.product_id
        uom = uom or self.import_uom_id
        factor = factor or self.import_uom_factor or 1.0
        fiscal_operation = fiscal_operation or self.fiscal_operation_id

        if self.import_state != "resolved":
            # The snapshot is taken ONCE, before the first conversion: a line
            # already resolved holds converted values, and snapshotting them
            # again would compound the factor on every new application.
            # partner_uom_code is the code declared by the counterparty
            # (filled by the importer or by the hook below) and is never
            # replaced by the internal unit here.
            self.write(
                {
                    "partner_uom_code": self.partner_uom_code
                    or self._get_partner_uom_code(),
                    "partner_quantity": self.quantity,
                    "partner_price_unit": self.price_unit,
                }
            )

        # The fallbacks keep a line whose supplier unit matched nothing
        # (uom_id empty, no snapshot ever written) from being converted
        # against zeros.
        declared_quantity = self.partner_quantity or self.quantity
        declared_price_unit = self.partner_price_unit or self.price_unit
        vals = {
            "import_state": "resolved",
            "import_uom_factor": factor,
            # Always convert from the declared values: the line total is
            # invariant (quantity times factor, unit price divided by it) and
            # re-applying with a factor of 1.0 restores what the counterparty
            # declared.
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
        self.write(vals)
        if product:
            self._find_or_create_supplierinfo()
        return True

    # Supplier nomenclature hooks: implemented by each fiscal document type
    # (e.g. l10n_br_nfe reads nfe40_cProd / nfe40_xProd / uCom).
    def _get_partner_product_code(self):
        self.ensure_one()
        return False

    def _get_partner_product_name(self):
        self.ensure_one()
        return False

    def _get_partner_uom_code(self):
        """Unit code as declared by the counterparty (e.g. the uCom of an
        NFe), which may have no equivalent in the company's own units.

        Importers that already persist it on ``partner_uom_code`` while
        parsing the file have nothing to override here.
        """
        self.ensure_one()
        return False

    def _get_partner_product_barcode(self):
        self.ensure_one()
        return False

    def _get_partner_product_ncm(self):
        self.ensure_one()
        return False

    def _prepare_product_vals(self):
        """Values of a product created from an imported line.

        Everything comes from what the supplier declared (the snapshot
        hooks), so the human reviewing the creation starts from the file
        instead of from a blank form: name, unit, seed price in the internal
        unit, barcode when it is a real GTIN and the NCM declared in the
        file.
        """
        self.ensure_one()
        # the internal unit the product is created in: the one the reviewer
        # chose (import_uom_id), else the unit the file already matched
        # (uom_id). When the supplier unit did not match any internal one
        # (e.g. a bag "SC" the company keeps in kg), neither is set and there
        # is nothing to guess: the reviewer must pick the internal unit first,
        # which is the supervised decision this whole flow is about.
        uom = self.import_uom_id or self.uom_id
        if not uom:
            raise UserError(
                _(
                    "Set the internal unit of measure on the line %(line)s "
                    "before creating the product: the supplier unit "
                    "(%(unit)s) does not match any internal unit, so the "
                    "conversion is a decision only a human can make."
                )
                % {
                    "line": self.name or self.id,
                    "unit": self.partner_uom_code or self.uom_id.name,
                }
            )
        # seed price comes from the supplier snapshot (the product does not
        # exist yet, so _get_supplierinfo_price has no product UoM to convert
        # against): the price the supplier charged, divided by the de-para
        # factor to reach the internal unit
        seed_price = self.partner_price_unit or self.price_unit
        if self.import_uom_factor:
            seed_price = seed_price / self.import_uom_factor
        vals = {
            "name": self._get_partner_product_name() or self.name,
            "uom_id": uom.id,
            "uom_po_id": uom.id,
            "standard_price": seed_price,
            "list_price": seed_price,
        }
        barcode = self._get_partner_product_barcode()
        if barcode and barcode != "SEM GTIN":
            in_use = self.env["product.product"].search_count(
                [("barcode", "=", barcode)]
            )
            if not in_use:
                vals["barcode"] = barcode
        ncm_code = self._get_partner_product_ncm()
        if ncm_code:
            ncm = self.env["l10n_br_fiscal.ncm"].search(
                [("code_unmasked", "=", ncm_code)], limit=1
            )
            if ncm:
                vals["ncm_id"] = ncm.id
        return vals

    def action_create_product_from_line(self):
        """Create the internal product from a pending imported line.

        Product creation is a SUPERVISED action: the user clicks, reviews
        the values seeded from the file and keeps ownership of the catalog.
        The created product resolves the line through the regular de-para
        path, which also learns the supplier info.
        """
        self.ensure_one()
        if self.product_id:
            raise UserError(
                _("The line %s already has an internal product.")
                % (self.name or self.id)
            )
        product = self.env["product.product"].create(self._prepare_product_vals())
        self._apply_import_depara(product=product)
        self.document_id.message_post(
            body=_("Product %(product)s created from imported line %(line)s.")
            % {"product": product.display_name, "line": self.name or self.id}
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "product.product",
            "res_id": product.id,
            "view_mode": "form",
            "target": "current",
        }

    def _suggest_product(self):
        """Suggest an internal product for an imported line.

        Priority: the supplier info de-para already learned for this partner
        and supplier code, then the internal reference, then the barcode.
        """
        self.ensure_one()
        product_model = self.env["product.product"]
        code = self._get_partner_product_code()
        partner = self.document_id.partner_id
        if code and partner:
            supplierinfo = self.env["product.supplierinfo"].search(
                [
                    ("partner_id", "=", partner.id),
                    ("product_code", "=", code),
                ],
                limit=1,
            )
            product = (
                supplierinfo.product_id
                or supplierinfo.product_tmpl_id.product_variant_id
            )
            if product:
                return product
        if code:
            product = product_model.search([("default_code", "=", code)], limit=1)
            if product:
                return product
        barcode = self._get_partner_product_barcode()
        if barcode and barcode != "SEM GTIN":
            product = product_model.search([("barcode", "=", barcode)], limit=1)
            if product:
                return product
        return product_model

    def _suggest_fiscal_operation_in(self):
        """Suggest the inbound fiscal operation of the line from the CFOP
        declared by the counterparty, through its inverse CFOP.

        The supplier declares an outbound CFOP (5xxx/6xxx/7xxx); the inverse
        CFOP (1xxx/2xxx/3xxx) is the company side of the same operation, and
        the approved operation lines referencing it tell which fiscal
        operations the company configured for that kind of entry.
        """
        self.ensure_one()
        cfop_inverse = self.partner_cfop_id.cfop_inverse_id
        if not cfop_inverse:
            return self.env["l10n_br_fiscal.operation"]
        operation_lines = self.env["l10n_br_fiscal.operation.line"].search(
            [
                ("state", "=", "approved"),
                ("fiscal_operation_type", "=", "in"),
                "|",
                "|",
                ("cfop_internal_id", "=", cfop_inverse.id),
                ("cfop_external_id", "=", cfop_inverse.id),
                ("cfop_export_id", "=", cfop_inverse.id),
            ]
        )
        return operation_lines[:1].fiscal_operation_id

    def _get_supplierinfo_price(self):
        """Price of the supplier info expressed in the product main UoM.

        The learning uses the CONVERTED unit price of the line, never the
        counterparty snapshot: the snapshot is expressed in the supplier
        unit, so with a conversion factor it would teach a price off by that
        very factor (a 25kg bag at 100 would be learned as 100/kg).
        """
        self.ensure_one()
        if not self.price_unit:
            return self.product_id.lst_price
        uom = self.import_uom_id or self.uom_id
        if uom:
            return uom._compute_price(self.price_unit, self.product_id.uom_id)
        return self.price_unit

    def _prepare_supplierinfo_vals(self):
        """Common supplier info values.

        Overriden by specialized document types (e.g. NFe) to add the
        partner UoM de-para values.
        """
        self.ensure_one()
        return {
            "product_id": self.product_id.id,
            "product_name": self._get_partner_product_name() or self.name,
            "product_code": self._get_partner_product_code(),
            "price": self._get_supplierinfo_price(),
        }

    def _find_or_create_supplierinfo(self):
        for line in self:
            partner = line.document_id.partner_id
            if not line.product_id or not partner:
                continue
            supplierinfo_model = line.env["product.supplierinfo"].with_company(
                line.company_id
            )
            supplierinfo = line.import_supplierinfo_id
            if not supplierinfo:
                # Adopt the de-para already learned for this partner, supplier
                # code and product (possibly by an earlier document): creating
                # a new record on every import would pile up duplicated
                # sellers on the product.
                supplierinfo = supplierinfo_model.search(
                    [
                        ("partner_id", "=", partner.id),
                        ("product_code", "=", line._get_partner_product_code()),
                        # a seller line entered by hand sits on the template,
                        # the one this method creates sits on the variant
                        "|",
                        ("product_id", "=", line.product_id.id),
                        (
                            "product_tmpl_id",
                            "=",
                            line.product_id.product_tmpl_id.id,
                        ),
                    ],
                    limit=1,
                )
            if supplierinfo:
                supplierinfo.write(line._prepare_supplierinfo_vals())
                line.import_supplierinfo_id = supplierinfo
            else:
                vals = line._prepare_supplierinfo_vals()
                vals["partner_id"] = partner.id
                line.import_supplierinfo_id = supplierinfo_model.create(vals)
                line.product_id.product_tmpl_id.seller_ids = [
                    fields.Command.link(line.import_supplierinfo_id.id)
                ]

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
