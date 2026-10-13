# Copyright 2025 Marcel Savegnago <https://escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from ..constants.fiscal import (
    TAX_DOMAIN_CBS,
    TAX_DOMAIN_IBS,
    TAX_RATE_TYPE,
    TAX_RATE_TYPE_DEFAULT,
)


class TaxClassification(models.Model):
    _name = "l10n_br_fiscal.tax.classification"
    _inherit = "l10n_br_fiscal.data.abstract"
    _order = "code"
    _description = "Tax Classification"

    code = fields.Char(size=8)

    description = fields.Text()

    cst_code_prefix_like = fields.Char(
        compute="_compute_cst_code_prefix_like",
        help="Helper field to filter taxes by CST code prefix (3 chars) using LIKE.",
    )

    @api.depends("code")
    def _compute_cst_code_prefix_like(self):
        for rec in self:
            prefix = (rec.code or "")[:3]
            # Avoid matching all records when the prefix is not available yet.
            rec.cst_code_prefix_like = (
                f"{prefix}%" if len(prefix) == 3 else "__no_match__%"
            )

    def _get_cst(self, tax_domain):
        """Return the IBS or CBS CST of the classification.

        The first three digits of the cClassTrib are the CST (IT 2025.002),
        and a CST that does not match them is rejected (rule UB14-20).
        """
        self.ensure_one()
        if not self.code or len(self.code) < 3:
            return self.env["l10n_br_fiscal.cst"]
        return self.env["l10n_br_fiscal.cst"].search(
            [("code", "=", self.code[:3]), ("tax_domain", "=", tax_domain)],
            limit=1,
        )

    @api.model
    def _tax_has_code_cst(self, tax, code):
        """Whether the tax has the CST of the cClassTrib (its 3 first digits)."""
        prefix = (code or "")[:3]
        return len(prefix) == 3 and prefix in (
            tax.cst_in_id.code,
            tax.cst_out_id.code,
        )

    def _load_records_write(self, values):
        # The data file refreshes the official table on every module update,
        # but the IBS/CBS taxes of a classification are configuration: keep
        # the ones already set, the user may have mapped them to other rates.
        # The file only replaces a tax without the cClassTrib CST by a tax
        # with it, which is how a wrong default of the file gets fixed.
        if self.env.context.get("install_module"):
            code = values.get("code") or self.code
            for field_name in ("tax_ibs_id", "tax_cbs_id"):
                current = self[field_name]
                if field_name not in values or not current:
                    continue
                new = self.env["l10n_br_fiscal.tax"].browse(values[field_name] or [])
                if (
                    new
                    and not self._tax_has_code_cst(current, code)
                    and self._tax_has_code_cst(new, code)
                ):
                    continue
                values.pop(field_name)
        return super()._load_records_write(values)

    tax_ibs_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax IBS",
        domain=(
            f"[('tax_domain', '=', '{TAX_DOMAIN_IBS}'), '|', "
            "('cst_in_id.code', 'like', cst_code_prefix_like), "
            "('cst_out_id.code', 'like', cst_code_prefix_like)]"
        ),
    )

    tax_cbs_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax CBS",
        domain=(
            f"[('tax_domain', '=', '{TAX_DOMAIN_CBS}'), '|', "
            "('cst_in_id.code', 'like', cst_code_prefix_like), "
            "('cst_out_id.code', 'like', cst_code_prefix_like)]"
        ),
    )

    regular_taxation = fields.Boolean(
        default=False,
    )

    presumed_credit = fields.Boolean(
        default=False,
    )

    credit_reversal = fields.Boolean(
        default=False,
    )

    rate_type = fields.Selection(
        selection=TAX_RATE_TYPE,
        default=TAX_RATE_TYPE_DEFAULT,
        required=True,
    )

    document_type_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.document.type",
        relation="tax_classification_document_type_rel",
        string="Related DFes",
        help="Related Digital Fiscal Documents",
    )
