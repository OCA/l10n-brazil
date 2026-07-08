# Copyright (C) 2021  Gabriel Cardoso de Faria - Kmee
# Copyright (C) 2023  Felipe Zago Rodrigues - Kmee
# Copyright 2025 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import Command, fields, models


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
