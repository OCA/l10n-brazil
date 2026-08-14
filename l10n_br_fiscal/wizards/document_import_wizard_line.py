# Copyright (C) 2021  Gabriel Cardoso de Faria - Kmee
# Copyright (C) 2023  Felipe Zago Rodrigues - Kmee
# Copyright 2025 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models

from ..tools import cfop_geography_warning


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
        """Compare the XML CFOP scope with the real issuer/company geography
        (see ``tools.cfop_geography_warning``)."""
        self.ensure_one()
        wizard = self.import_xml_id
        return cfop_geography_warning(
            self.cfop_xml,
            wizard.issuer_partner_id,
            wizard.company_id,
        )
