# Copyright (C) 2026 - TODAY, KMEE (<https://kmee.com.br>)
# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models

from ..constants.duimp import DUIMP_UOM_XMLID


class L10nBrDuimpItem(models.Model):
    """DUIMP item with per-item taxes and cost allocation."""

    _name = "l10n_br_duimp.item"
    _inherit = "l10n_br_duimp.mixin"
    _description = "DUIMP Item"
    _order = "declaration_id, item_number"

    def name_get(self):
        """Without this the item shows up as "l10n_br_duimp.item,36"
        wherever it is referenced, e.g. in the per-item tax breakdown."""
        result = []
        for item in self:
            label = _("Item %s") % (item.item_number or "?")
            detail = item.product_id.display_name or item.product_code
            if detail:
                label = f"{label} - {detail}"
            result.append((item.id, label))
        return result

    declaration_id = fields.Many2one(
        comodel_name="l10n_br_duimp.declaration",
        string="Declaration",
        required=True,
        ondelete="cascade",
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        related="declaration_id.company_id",
        store=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="declaration_id.currency_id",
    )

    item_number = fields.Char(string="Item No.", index=True)
    product_code = fields.Char(string="DUIMP Product Code")
    ncm_code = fields.Char(string="NCM")
    description = fields.Char()
    exporter_code = fields.Char(
        help="exportador.codigo (CATP operator code, e.g. OPE_3). The "
        "payload carries no exporter name, so this code is what a partner "
        "de-para can be built on (res.partner.ref).",
    )
    siscomex_fee = fields.Monetary(
        string="Siscomex Fee (item)",
        help="tributos.mercadoria.taxaUtilizacao reported for this item.",
    )

    quantity = fields.Float(digits="Product Unit of Measure")
    trade_uom = fields.Char(string="Traded UoM")

    trade_currency_id = fields.Many2one(
        comodel_name="res.currency", string="Negotiated Currency"
    )
    exchange_rate = fields.Float(digits=(12, 8))

    trade_unit_value = fields.Float(
        string="Unit Price (Currency)",
        digits=(12, 8),
        help="Unit price in the negotiated currency, when the DUIMP "
        "reports it; otherwise 0.",
    )
    product_id = fields.Many2one(comodel_name="product.product", string="Product")
    uom_id = fields.Many2one(comodel_name="uom.uom", string="Unit of Measure")
    cfop_id = fields.Many2one(comodel_name="l10n_br_fiscal.cfop", string="CFOP")
    price_unit = fields.Monetary(
        string="Unit Price (BRL)",
        help="Unit price already converted to BRL.",
    )
    merchandise_value = fields.Monetary()
    customs_value = fields.Monetary()
    allocated_freight = fields.Monetary()
    allocated_insurance = fields.Monetary()
    addition_deduction_ids = fields.One2many(
        comodel_name="l10n_br_duimp.addition.deduction",
        inverse_name="item_id",
        string="Additions/Deductions",
    )
    tax_ids = fields.One2many(
        comodel_name="l10n_br_duimp.item.tax",
        inverse_name="item_id",
        string="Taxes",
    )
    addition_deduction = fields.Monetary(
        string="Additions/Deductions (BRL)", compute="_compute_totals", store=True
    )
    unit_addition_deduction = fields.Monetary(
        string="Unit Additions/Deductions", compute="_compute_totals", store=True
    )
    amount_afrmm = fields.Monetary(
        string="AFRMM", compute="_compute_totals", store=True
    )
    amount_siscomex = fields.Monetary(
        string="Siscomex Fee", compute="_compute_totals", store=True
    )
    amount_capatazia = fields.Monetary(
        string="Capatazia", compute="_compute_totals", store=True
    )
    amount_other = fields.Monetary(
        string="Other Costs",
        compute="_compute_totals",
        store=True,
        help="AFRMM + Siscomex fee + capatazia allocated to this item. "
        "Booked as 'other value' on the generated invoice line.",
    )
    final_price_unit = fields.Monetary(
        string="Final Unit Price",
        compute="_compute_totals",
        store=True,
        help="Unit price in BRL including the allocated additions/"
        "deductions (used as price_unit of the generated invoice line).",
    )
    amount_total = fields.Monetary(
        string="Total", compute="_compute_totals", store=True
    )

    @api.depends(
        "quantity",
        "price_unit",
        "customs_value",
        "addition_deduction_ids.amount",
        "declaration_id.afrmm_amount",
        "declaration_id.siscomex_fee_amount",
        "declaration_id.handling_fee_amount",
        "declaration_id.total_customs_value",
    )
    def _compute_totals(self):
        for line in self:
            declaration = line.declaration_id
            line.addition_deduction = sum(line.addition_deduction_ids.mapped("amount"))
            line.unit_addition_deduction = (
                line.addition_deduction / line.quantity if line.quantity else 0.0
            )
            total_customs_value = declaration.total_customs_value
            proportion = (
                (line.customs_value / total_customs_value)
                if total_customs_value
                else 0.0
            )
            line.amount_afrmm = proportion * declaration.afrmm_amount
            line.amount_siscomex = proportion * declaration.siscomex_fee_amount
            line.amount_capatazia = proportion * declaration.handling_fee_amount
            line.amount_other = (
                line.amount_afrmm + line.amount_siscomex + line.amount_capatazia
            )

            line.final_price_unit = line.price_unit + line.unit_addition_deduction
            line.amount_total = line.final_price_unit * line.quantity

    def _match_product(self):
        """Auto-match the internal product from the DUIMP item.

        Only unambiguous matches are applied. The DUIMP product code comes
        from the importer's own catalogue (CATP) and is often very short
        ("38", "39"), so an ``ilike`` on it would happily match an
        unrelated product; and an NCM is shared by many products by
        definition. A guess here is silent and ends up on the vendor bill,
        so whatever is ambiguous is left for the user to pick.
        """
        Product = self.env["product.product"]
        for line in self:
            if line.product_id:
                continue
            product = Product.browse()
            if line.product_code:
                product = Product.search(
                    [("default_code", "=", line.product_code)], limit=1
                ) or Product.search([("barcode", "=", line.product_code)], limit=1)
            if not product and line.ncm_code:
                candidates = Product.search(
                    [("ncm_id.code_unmasked", "=", line.ncm_code)], limit=2
                )
                # exactly one product with this NCM: unambiguous
                product = candidates if len(candidates) == 1 else Product.browse()
            if product:
                line.product_id = product
                if not line.uom_id and product.uom_id:
                    line.uom_id = product.uom_id
        self._match_uom()

    def _match_uom(self):
        """Map the Siscomex commercial unit to an Odoo unit of measure.

        Only used when the matched product does not already impose one:
        the product's own unit is what the rest of the purchase flow
        expects. A unit that is not in the de-para is left empty for the
        user to pick, since inventing one silently changes the quantity
        the vendor bill carries.
        """
        for line in self:
            if line.uom_id or not line.trade_uom:
                continue
            xmlid = DUIMP_UOM_XMLID.get(line.trade_uom.strip().upper())
            if not xmlid:
                continue
            uom = self.env.ref(xmlid, raise_if_not_found=False)
            if uom:
                line.uom_id = uom
