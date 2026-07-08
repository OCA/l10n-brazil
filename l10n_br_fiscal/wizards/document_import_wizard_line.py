# Copyright (C) 2021  Gabriel Cardoso de Faria - Kmee
# Copyright (C) 2023  Felipe Zago Rodrigues - Kmee
# Copyright 2025 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import Command, _, api, fields, models


class DocumentImportWizardLine(models.TransientModel):
    """Generic line of the fiscal document import wizard.

    This model holds the document-type agnostic data of an imported
    fiscal document line so the "de-para" (matching between the supplier
    nomenclature coming from the XML and the company's own fiscal settings)
    can be reviewed before the fiscal document and the account move are
    actually created.

    It is meant to be extended (via ``_inherit``) by each specialized fiscal
    document importer (NFe, and CTe in the future) to add the fields and the
    behavior that are specific to that document type (e.g. NFe taxes or the
    commercial/tax unit split).
    """

    _name = "l10n_br_fiscal.document.import.wizard.line"
    _description = "Fiscal Document Import Wizard Line"

    import_xml_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.import.wizard",
    )

    imported_partner_id = fields.Many2one(related="import_xml_id.partner_id")

    # XML (supplier nomenclature) data:
    product_name = fields.Char()

    product_code = fields.Char(string="XML Product Code")

    ncm_xml = fields.Char(string="XML NCM Code")

    cfop_xml = fields.Char(string="XML CFOP")

    uom_com = fields.Char(string="UOM Comercial")

    quantity_com = fields.Float(string="Comercial Quantity")

    price_unit_com = fields.Float(string="Comercial Price Unit")

    total = fields.Float()

    # Internal (company fiscal settings) data used for the de-para:
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product Internal Reference",
    )

    product_supplier_id = fields.Many2one(
        comodel_name="product.supplierinfo",
        string="Product Supplier",
    )

    uom_internal = fields.Many2one(
        comodel_name="uom.uom",
        help="Internal UoM, equivalent to the comercial one in the document",
    )

    uom_conversion_factor = fields.Float(string="UOM Conversion Factor", default=1)

    ncm_internal = fields.Char(
        related="product_id.ncm_id.code",
        string="Internal NCM Code",
    )

    new_cfop_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cfop",
        string="Change CFOP",
    )

    cfop_warning = fields.Char(
        compute="_compute_cfop_warning",
        string="CFOP Alert",
        help="Warns when the CFOP declared in the XML is inconsistent with "
        "the actual geography (issuer state vs company state). Useful to "
        "spot supplier mistakes before they pollute the SPED books.",
    )

    @api.depends("cfop_xml", "import_xml_id.issuer_partner_id.state_id")
    def _compute_cfop_warning(self):
        for line in self:
            line.cfop_warning = line._get_cfop_warning()

    def _get_cfop_warning(self):
        """Compare the XML CFOP scope (from its first digit) with the real
        issuer/company geography. CFOP first digit: 1/5 = intrastate,
        2/6 = interstate, 3/7 = foreign trade."""
        self.ensure_one()
        if not self.cfop_xml:
            return False
        declared = self.cfop_xml[0]
        wizard = self.import_xml_id
        issuer_state = wizard.issuer_partner_id.state_id
        company_state = wizard.company_id.state_id
        if not issuer_state or not company_state:
            return False
        same_state = issuer_state == company_state
        if declared in ("1", "5") and not same_state:
            return _(
                "XML CFOP %(cfop)s is intrastate but issuer (%(issuer)s) "
                "and company (%(company)s) are in different states."
            ) % {
                "cfop": self.cfop_xml,
                "issuer": issuer_state.code,
                "company": company_state.code,
            }
        if declared in ("2", "6") and same_state:
            return _(
                "XML CFOP %(cfop)s is interstate but issuer "
                "and company are both in %(state)s."
            ) % {"cfop": self.cfop_xml, "state": company_state.code}
        return False

    def _find_or_create_product_supplierinfo(self):
        for line in self:
            if not line.product_id:
                continue

            if not line.product_supplier_id:
                line._create_product_supplier()
            else:
                line._update_product_supplier()

    def _get_supplierinfo_price(self):
        """Price of the supplierinfo expressed in the product main UoM."""
        if self.uom_internal:
            return self.uom_internal._compute_price(
                self.price_unit_com, self.product_id.uom_id
            )
        return self.product_id.lst_price

    def _prepare_supplierinfo_vals(self):
        """Common supplierinfo values.

        Overriden by specialized document types (e.g. NFe) to add the
        partner UoM de-para values.
        """
        return {
            "product_id": self.product_id.id,
            "product_name": self.product_name,
            "product_code": self.product_code,
            "price": self._get_supplierinfo_price(),
        }

    def _create_product_supplier(self):
        vals = self._prepare_supplierinfo_vals()
        vals["partner_id"] = self.imported_partner_id.id
        self.product_supplier_id = self.env["product.supplierinfo"].create(vals)
        self.product_id.write(
            {"seller_ids": [Command.link(self.product_supplier_id.id)]}
        )

    def _update_product_supplier(self):
        self.product_supplier_id.write(self._prepare_supplierinfo_vals())
