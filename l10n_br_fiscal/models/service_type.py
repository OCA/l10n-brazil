# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ServiceType(models.Model):
    _name = "l10n_br_fiscal.service.type"
    _inherit = ["l10n_br_fiscal.data.abstract", "mail.thread", "mail.activity.mixin"]
    _description = "Service Fiscal Type"

    parent_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.service.type", string="Parent Service Type"
    )

    child_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.service.type",
        inverse_name="parent_id",
        string="Service Type Child",
    )

    internal_type = fields.Selection(
        selection=[("view", "View"), ("normal", "Normal")],
        string="Internal Type",
        required=True,
        default="normal",
    )

    product_tmpl_ids = fields.One2many(
        comodel_name="product.template",
        string="Products",
        compute="_compute_product_tmpl_info",
    )

    product_tmpl_qty = fields.Integer(
        string="Products Quantity", compute="_compute_product_tmpl_info"
    )

    def _compute_product_tmpl_info(self):
        for record in self:
            product_tmpls = record.env["product.template"].search(
                [
                    ("service_type_id", "=", record.id),
                    "|",
                    ("active", "=", False),
                    ("active", "=", True),
                ]
            )
            record.product_tmpl_ids = product_tmpls
            record.product_tmpl_qty = len(product_tmpls)
