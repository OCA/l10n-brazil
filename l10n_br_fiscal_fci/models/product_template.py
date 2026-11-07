# Copyright (C) 2026  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    fci_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.fci",
        inverse_name="product_tmpl_id",
        string="FCI",
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

    @api.depends("fci_ids.fci_code", "fci_ids.state")
    def _compute_fci_code(self):
        for product in self:
            fcis = product.fci_ids.filtered(
                lambda fci: fci.company_id == self.env.company
            )
            product.fci_count = len(fcis)
            with_code = fcis.filtered("fci_code").sorted(
                key=lambda fci: fci.fci_file_id.date, reverse=True
            )
            product.fci_code = with_code[:1].fci_code

    def action_view_fci(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "l10n_br_fiscal_fci.fci_action"
        )
        action["domain"] = [("product_tmpl_id", "=", self.id)]
        action["context"] = {"search_default_group_fci": 1}
        action["display_name"] = _("FCI of %s") % self.display_name
        return action
