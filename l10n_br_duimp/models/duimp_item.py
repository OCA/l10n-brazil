# Copyright (C) 2026 - TODAY, KMEE (<https://kmee.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class L10nBrDuimpItem(models.Model):
    """A single DUIMP item.

    The DUIMP taxes merchandise **per item** (unlike the DI, which groups
    it into "adições"), so this model merges the two DI concepts
    ``l10n_br_di.adicao`` and ``l10n_br_di.mercadoria`` into one. The
    proportional-allocation maths (additions/deductions, Siscomex fee,
    AFRMM, capatazia → ``final_price_unit``/``amount_other``) is ported
    from ``l10n_br_di.mercadoria._compute_totals`` (KMEE 14.0); what
    changes is the allocation base: the DI rateava por adição, the DUIMP
    rateia por item sobre o valor aduaneiro total da declaração.
    """

    _name = "l10n_br_duimp.item"
    _inherit = "l10n_br_duimp.mixin"
    _description = "DUIMP Item"
    _order = "declaracao_id, numero_item"

    declaracao_id = fields.Many2one(
        comodel_name="l10n_br_duimp.declaracao",
        string="Declaration",
        required=True,
        ondelete="cascade",
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        related="declaracao_id.company_id",
        store=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="declaracao_id.currency_id",
    )

    # --- Data returned by the DUIMP payload -----------------------------
    numero_item = fields.Char(string="Item No.", index=True)
    codigo_produto = fields.Char(
        string="DUIMP Product Code",
        help="codigoProduto from the importer's own product catalogue "
        "(CATP). Used to auto-match the internal product.",
    )
    ncm_codigo = fields.Char(string="NCM")
    descricao = fields.Char(string="Description")

    quantidade = fields.Float(string="Quantity", digits="Product Unit of Measure")
    unidade_comercializada = fields.Char(string="Traded UoM")

    moeda_venda_id = fields.Many2one(
        comodel_name="res.currency", string="Negotiated Currency"
    )
    taxa_cambio_venda = fields.Float(string="Exchange Rate", digits=(12, 8))

    valor_unitario = fields.Float(
        string="Unit Price (Currency)",
        digits=(12, 8),
        help="Unit price in the negotiated currency, when the DUIMP "
        "reports it; otherwise 0.",
    )

    # --- De-para (item ↔ internal Odoo records) -------------------------
    product_id = fields.Many2one(comodel_name="product.product", string="Product")
    uom_id = fields.Many2one(comodel_name="uom.uom", string="Unit of Measure")
    cfop_id = fields.Many2one(comodel_name="l10n_br_fiscal.cfop", string="CFOP")

    # --- Monetary values already in BRL (from the DUIMP payload) --------
    price_unit = fields.Monetary(
        string="Unit Price (BRL)",
        help="Unit price already converted to BRL.",
    )
    valor_mercadoria = fields.Monetary(string="Merchandise Value")
    valor_aduaneiro = fields.Monetary(
        string="Customs Value",
        help="II (Import Duty) tax base reported by the DUIMP; used as "
        "the allocation base for header-level costs and taxes.",
    )
    valor_frete_rateado = fields.Monetary(string="Allocated Freight")
    valor_seguro_rateado = fields.Monetary(string="Allocated Insurance")

    # --- Relations ------------------------------------------------------
    acrescimo_deducao_ids = fields.One2many(
        comodel_name="l10n_br_duimp.acrescimo.deducao",
        inverse_name="item_id",
        string="Additions/Deductions",
    )
    tributo_ids = fields.One2many(
        comodel_name="l10n_br_duimp.item.tributo",
        inverse_name="item_id",
        string="Tributes",
    )

    # --- Computed allocation (ported from l10n_br_di.mercadoria) --------
    amount_subtotal_brl = fields.Monetary(
        string="Subtotal (BRL)", compute="_compute_totals", store=True
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
        "quantidade",
        "price_unit",
        "valor_aduaneiro",
        "acrescimo_deducao_ids.valor",
        "declaracao_id.afrmm_total",
        "declaracao_id.taxa_siscomex_total",
        "declaracao_id.capatazia_total",
        "declaracao_id.total_valor_aduaneiro",
    )
    def _compute_totals(self):
        for line in self:
            declaracao = line.declaracao_id
            line.amount_subtotal_brl = line.quantidade * line.price_unit

            line.addition_deduction = sum(line.acrescimo_deducao_ids.mapped("valor"))
            line.unit_addition_deduction = (
                line.addition_deduction / line.quantidade if line.quantidade else 0.0
            )

            # Header-level costs are allocated proportionally to the item's
            # customs value (valorAduaneiro), the same base Siscomex uses.
            total_aduaneiro = declaracao.total_valor_aduaneiro
            proportion = (
                (line.valor_aduaneiro / total_aduaneiro) if total_aduaneiro else 0.0
            )
            line.amount_afrmm = proportion * declaracao.afrmm_total
            line.amount_siscomex = proportion * declaracao.taxa_siscomex_total
            line.amount_capatazia = proportion * declaracao.capatazia_total
            line.amount_other = (
                line.amount_afrmm + line.amount_siscomex + line.amount_capatazia
            )

            line.final_price_unit = line.price_unit + line.unit_addition_deduction
            line.amount_total = line.final_price_unit * line.quantidade

    def _match_product(self):
        """Auto-match the internal product from the DUIMP ``codigoProduto``
        (CATP) and NCM.

        Implements the auto-match the DI left as a TODO
        (``l10n_br_di.mercadoria._match_product_unit``). The DUIMP makes
        it feasible because every item carries the importer's own product
        code. Full CATP catalogue sync is phase 2; here we only read the
        code to reconcile against existing products.
        """
        Product = self.env["product.product"]
        for line in self:
            if line.product_id:
                continue
            product = Product.browse()
            if line.codigo_produto:
                product = Product.search(
                    [("default_code", "=", line.codigo_produto)], limit=1
                ) or Product.search([("barcode", "=", line.codigo_produto)], limit=1)
            if not product and line.ncm_codigo:
                product = Product.search(
                    [("ncm_id.code_unmasked", "=", line.ncm_codigo)], limit=1
                )
            if product:
                line.product_id = product
                if not line.uom_id:
                    line.uom_id = product.uom_id
