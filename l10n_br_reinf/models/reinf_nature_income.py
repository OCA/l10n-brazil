# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..constants import REINF_TAX_WITHHOLDING_FLAG


class ReinfNatureIncome(models.Model):
    """Nature of income (natRend) of the R-4010 and of the R-4020.

    It inherits l10n_br_fiscal.data.abstract, which already brings code, name,
    active, the date_start / date_end validity and the "<code> - <name>"
    display, the same way every other fiscal table of the localization does.

    The flags say which withholdings the nature may carry. They are a property
    of the nature, not of the partner: the same supplier can be paid under two
    natures in the same month, with different withholdings. And they are not
    typed by hand: they are read from the mapping of the Annex I, so the flag
    and the revenue code can never tell different stories.
    """

    _name = "l10n_br_reinf.nature.income"
    _inherit = ["l10n_br_fiscal.data.abstract"]
    _description = "EFD-Reinf Nature of Income"

    admitted_taxes = fields.Char(
        help="Taxes this nature admits, as the column Tributo of the Tabela 01 "
        "gives it. It is the authorization of the aggregated withholding AND "
        "the list of components the aggregate carries, which is not always the "
        "three: the cooperatives of work of the nature 15001 admit "
        "IR, COFINS, PP, AGREGADO, with no CSLL.",
    )

    tax_ids = fields.One2many(
        comodel_name="l10n_br_reinf.nature.income.tax",
        inverse_name="nature_income_id",
        string="Taxes and Revenue Codes",
    )

    ret_ir = fields.Boolean(
        string="Income Tax",
        compute="_compute_withholding_flags",
        store=True,
        help="The nature is subject to the withholding of income tax (IRPF, "
        "IRPJ or RRA).",
    )

    ret_agreg = fields.Boolean(
        string="Aggregated",
        compute="_compute_withholding_flags",
        store=True,
        help="The withholdings of CSLL, PIS/PASEP and COFINS may be declared "
        "aggregated in a single value, under a single revenue code.",
    )

    ret_csll = fields.Boolean(
        string="CSLL",
        compute="_compute_withholding_flags",
        store=True,
        help="The nature is subject to the withholding of CSLL.",
    )

    ret_cofins = fields.Boolean(
        string="COFINS",
        compute="_compute_withholding_flags",
        store=True,
        help="The nature is subject to the withholding of COFINS.",
    )

    ret_pp = fields.Boolean(
        string="PIS/PASEP",
        compute="_compute_withholding_flags",
        store=True,
        help="The nature is subject to the withholding of PIS/PASEP.",
    )

    @api.depends("tax_ids.tax_type")
    def _compute_withholding_flags(self):
        flags = set(REINF_TAX_WITHHOLDING_FLAG.values())
        for record in self:
            raised = {
                REINF_TAX_WITHHOLDING_FLAG[tax_type]
                for tax_type in record.tax_ids.mapped("tax_type")
                if tax_type in REINF_TAX_WITHHOLDING_FLAG
            }
            for flag in flags:
                record[flag] = flag in raised

    _sql_constraints = [
        (
            "reinf_nature_income_code_uniq",
            "unique (code)",
            "The nature of income code must be unique.",
        )
    ]

    @api.constrains("code")
    def _check_code(self):
        for record in self:
            code = record.code or ""
            if len(code) != 5 or not code.isdigit():
                raise ValidationError(
                    _(
                        "The nature of income %(code)s is not valid: the layout "
                        "asks for exactly 5 digits.",
                        code=code,
                    )
                )
