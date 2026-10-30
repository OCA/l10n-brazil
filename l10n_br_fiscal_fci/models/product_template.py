# Copyright (C) 2026  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    fci_line_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.fci.line",
        inverse_name="product_tmpl_id",
        string="FCI Lines",
        readonly=True,
    )

    fci_code = fields.Char(
        string="FCI Control Number",
        compute="_compute_fci_code",
        help="Last FCI control number generated for this product in the "
        "current company. It must be written in the NF-e field nFCI of the "
        "interstate operations with this product.",
    )

    fci_count = fields.Integer(
        string="FCI Count",
        compute="_compute_fci_code",
    )

    @api.depends("fci_line_ids.fci_code", "fci_line_ids.state")
    def _compute_fci_code(self):
        for product in self:
            lines = product.fci_line_ids.filtered(
                lambda line: line.company_id == self.env.company
            )
            product.fci_count = len(lines)
            with_code = lines.filtered("fci_code").sorted(
                key=lambda line: line.fci_id.date, reverse=True
            )
            product.fci_code = with_code[:1].fci_code

    def action_view_fci(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "l10n_br_fiscal_fci.fci_line_action"
        )
        action["domain"] = [("product_tmpl_id", "=", self.id)]
        action["context"] = {"search_default_group_fci": 1}
        action["display_name"] = _("FCI of %s") % self.display_name
        return action
