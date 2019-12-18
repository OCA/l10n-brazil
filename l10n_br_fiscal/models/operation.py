# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..constants.fiscal import (
    OPERATION_FISCAL_TYPE,
    OPERATION_FISCAL_TYPE_DEFAULT,
    FISCAL_IN_OUT_ALL,
    CFOP_TYPE_MOVE,
    CFOP_TYPE_MOVE_DEFAULT,
    OPERATION_STATE_DEFAULT,
    OPERATION_STATE
)


class Operation(models.Model):
    _name = "l10n_br_fiscal.operation"
    _description = "Fiscal Operation"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    code = fields.Char(
        string="Code",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    name = fields.Char(
        string="Name",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    operation_type = fields.Selection(
        selection=FISCAL_IN_OUT_ALL,
        string="Type",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    document_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.type",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    document_electronic = fields.Boolean(
        related="document_type_id.electronic", string="Electronic?"
    )

    document_serie_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.serie",
        readonly=True,
        states={"draft": [("readonly", False)]},
        domain="[('active', '=', True)," "('document_type_id', '=', document_type_id)]",
    )

    default_price_unit = fields.Selection(
        selection=[("sale_price", _("Sale Price")), ("cost_price", _("Cost Price"))],
        string="Default Price Unit?",
        default="sale_price",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    fiscal_type = fields.Selection(
        selection=OPERATION_FISCAL_TYPE,
        string="Fiscal Type",
        default=OPERATION_FISCAL_TYPE_DEFAULT,
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    return_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Return Operation",
        readonly=True,
        states={"draft": [("readonly", False)]},
        domain="[('operation_type', '!=', operation_type), ('fiscal_type', 'in', {'sale': ['sale_return'], 'purchase': "
               "['purchase_return'], 'other': ['return_in', 'return_out']}.get("
               "fiscal_type, []))]"
    )

    inverse_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Inverse Operation",
        domain="[('operation_type', '!=', operation_type), ('fiscal_type', '!=', fiscal_type)]",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    state = fields.Selection(
        selection=OPERATION_STATE,
        string="State",
        default=OPERATION_STATE_DEFAULT,
        index=True,
        readonly=True,
        track_visibility="onchange",
        copy=False,
    )

    line_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.operation.line",
        inverse_name="operation_id",
        string="Operation Line",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="l10n_br_fiscal_operation_line_comment_rel",
        column1="operation_id",
        column2="comment_id",
        string="Comment",
    )

    _sql_constraints = [
        (
            "fiscal_operation_code_uniq",
            "unique (code)",
            _("Fiscal Operation already exists with this code !"),
        )
    ]

    @api.multi
    def action_review(self):
        self.write({"state": "review"})
        self.line_ids.write({"state": "review"})

    @api.multi
    def action_approve(self):
        self.write({"state": "approved"})
        self.line_ids.write({"state": "approved"})

    @api.multi
    def action_draft(self):
        self.write({"state": "draft"})
        self.line_ids.write({"state": "draft"})

    @api.multi
    def unlink(self):
        operations = self.filtered(lambda l: l.state == "approved")
        if operations:
            raise UserError(_("You cannot delete an Operation which is not draft !"))
        return super(Operation, self).unlink()

    def _line_domain(self, company, partner, product):

        domain = [
            ("operation_id", "=", self.id),
            ("operation_type", "=", self.operation_type),
            ("state", "=", "approved"),
        ]

        domain += [
            "|",
            ("company_tax_framework", "=", company.tax_framework),
            ("company_tax_framework", "=", False),
        ]

        domain += [
            "|",
            ("partner_tax_framework", "=", partner.tax_framework),
            ("partner_tax_framework", "=", False),
        ]

        domain += [
            "|",
            ("product_type", "=", product.fiscal_type),
            ("product_type", "=", False),
        ]

        return domain

    @api.multi
    def line_definition(self, company, partner, product):
        self.ensure_one()
        if not company:
            company = self.env.user.company_id

        line = self.line_ids.search(
            self._line_domain(company, partner, product), limit=1
        )

        return line
