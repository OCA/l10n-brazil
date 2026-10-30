# Copyright (C) 2018  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, fields, models

from ..constants.fiscal import FISCAL_IN_OUT_ALL


class CST(models.Model):
    _name = "l10n_br_fiscal.cst"
    _inherit = "l10n_br_fiscal.data.abstract"
    _order = "tax_domain, code"
    _description = "CST"

    code = fields.Char(size=4)

    cst_type = fields.Selection(
        selection=FISCAL_IN_OUT_ALL, string="Type", required=True
    )

    tax_group_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.group",
        string="Fiscal Tax Group",
        required=True,
    )

    tax_domain = fields.Selection(
        related="tax_group_id.tax_domain",
        string="Tax Domain",
        store=True,
    )

    default_creditable_tax = fields.Boolean(
        string="Creditable Tax Default?",
        default=False,
        help="Whether this CST allows an input tax credit by its own nature.\n\n"
        "Defaults to False so a tax rule fails closed: a CST created later, or"
        " one whose meaning is residual, does not silently take a credit and"
        " leave the tax out of the stock acquisition cost. The CSTs that do"
        " grant a credit state it in the data file.",
    )

    _sql_constraints = [
        (
            "l10n_br_fiscal_cst_code_tax_group_id_uniq",
            "unique (code, tax_group_id)",
            _("CST already exists with this code !"),
        )
    ]
