# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import FISCAL_TAX_ID_FIELDS


class ContractLine(models.Model):
    _name = "contract.line"
    _inherit = [_name, "l10n_br_fiscal.document.line.mixin"]

    country_id = fields.Many2one(related="company_id.country_id", store=True)

    fiscal_tax_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.tax",
        relation="fiscal_contract_line_tax_rel",
        column1="document_id",
        column2="fiscal_tax_id",
        string="Fiscal Taxes",
    )

    tax_framework = fields.Selection(
        related="contract_id.company_id.tax_framework",
        string="Tax Framework",
    )

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        related="contract_id.partner_id",
        string="Partner",
        store=True,
        precompute=True,
    )

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="contract_line_comment_rel",
        column1="contract_line_id",
        column2="comment_id",
        string="Comments",
    )

    line_recurrence = fields.Boolean(related="contract_id.line_recurrence")

    # adapted for _compute_find_final:
    def _get_document(self):
        self.ensure_one()
        return self.contract_id

    def _setup_complete(self):
        # Same approach as l10n_br_purchase: mixin fields use precompute=True but
        # contract lines do not have all dependencies ready at create time.
        res = super()._setup_complete()
        mixin = self.env["l10n_br_fiscal.document.line.mixin"]
        mixin_fields = mixin._fields
        for name, field in self._fields.items():
            mixin_field = mixin_fields.get(name)
            if not mixin_field:
                continue
            if mixin_field.compute in (
                "_compute_price_unit_fiscal",
                "_compute_product_fiscal_fields",
                "_compute_fiscal_quantity",
                "_compute_fiscal_price",
                "_compute_fiscal_tax_ids",
                "_compute_tax_fields",
                "_compute_fiscal_operation_line_id",
                "_compute_comment_ids",
            ) and getattr(mixin_field, "precompute", False):
                field.precompute = False
        return res

    def _needs_fiscal_tax_recompute(self, vals):
        return "fiscal_tax_ids" in vals or any(
            fname in vals for fname in FISCAL_TAX_ID_FIELDS
        )

    def _recompute_fiscal_tax_fields(self):
        # _compute_tax_fields writes tax outputs; skip re-entry via write().
        self.with_context(skip_fiscal_tax_recompute=True)._compute_tax_fields()

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        # Form save often creates with fiscal_tax_ids + *_tax_id together;
        # the mixin compute can run before both values settle and leave
        # amount_tax_withholding at 0. Force a final recompute.
        if any(self._needs_fiscal_tax_recompute(vals) for vals in vals_list):
            lines._recompute_fiscal_tax_fields()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get("skip_fiscal_tax_recompute"):
            return res
        # Same race as create: writing inss_wh_tax_id together with
        # fiscal_tax_ids can make _compute_tax_fields run on stale taxes
        # and persist amount_tax_withholding=0 after an onchange showed 11.
        if self._needs_fiscal_tax_recompute(vals):
            self._recompute_fiscal_tax_fields()
        return res

    def _prepare_invoice_line(self):
        self.ensure_one()

        contract = self.contract_id
        invoice_line_vals = super()._prepare_invoice_line()

        # Por algum motivo com a localização o campo company_currency_id
        # nao vem em invoice_line_val e isto impacta com o modulo contract
        invoice_line_vals.update(
            {"company_currency_id": contract.company_id.currency_id.id}
        )

        quantity = invoice_line_vals.get("quantity")

        tax_ids = self.fiscal_tax_ids.account_taxes(
            user_type=contract.contract_type,
            fiscal_operation=contract.fiscal_operation_id,
            company=contract.company_id,
        )

        if invoice_line_vals:
            invoice_line_vals.update(self._prepare_br_fiscal_dict())
            invoice_line_vals["quantity"] = quantity
            invoice_line_vals["tax_ids"] = tax_ids.ids
        return invoice_line_vals
