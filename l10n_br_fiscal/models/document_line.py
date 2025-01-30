# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class DocumentLine(models.Model):
    _name = "l10n_br_fiscal.document.line"
    _inherit = "l10n_br_fiscal.document.line.mixin"
    _description = "Fiscal Document Line"

    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Document",
        ondelete="cascade",
    )

    name = fields.Char()

    default_code = fields.Char()

    company_id = fields.Many2one(
        comodel_name="res.company",
        related="document_id.company_id",
        store=True,
        string="Company",
    )

    tax_framework = fields.Selection(
        related="company_id.tax_framework",
    )

    partner_id = fields.Many2one(
        related="document_id.partner_id",
        store=True,
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="company_id.currency_id",
        string="Currency",
    )

    ind_final = fields.Selection(related="document_id.ind_final")

    # Usado para tornar Somente Leitura os campos dos custos
    # de entrega quando a definição for por Total
    delivery_costs = fields.Selection(
        related="company_id.delivery_costs",
    )

    force_compute_delivery_costs_by_total = fields.Boolean(
        related="document_id.force_compute_delivery_costs_by_total"
    )

    edoc_purpose = fields.Selection(
        related="document_id.edoc_purpose",
    )

    imported_document = fields.Boolean(
        related="document_id.imported_document",
    )

    line_product_import_state = fields.Selection(
        selection=[
            ("create_product", "Create Product"),
            ("assign_product", "Assigin Product"),
            ("assigned_product", "Assigined Product"),
        ],
        default="create_product",
        string="Default Import State",
    )

    line_import_state = fields.Selection(
        selection=[
            ("create_product", "Create Product"),
            ("assign_product", "Assigin Product"),
            ("assigned_product", "Assigined Product"),
        ],
        default="create_product",
        string="Default Import State",
    )

    line_import_message = fields.Char(
        compute="_compute_line_import_status",
    )
