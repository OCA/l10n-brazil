# Copyright (C) 2022  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class Service(models.Model):
    _name = "l10n_br_fiscal_edi.service"
    _inherit = "l10n_br_fiscal.data.abstract"
    _description = "Generic Fiscal Service"

    name = fields.Char(required=True, index=True)

    description = fields.Text(required=True, index=True)

    document_type_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.document.type",
        string="Document Type",
    )

    service_message_ids = fields.One2many(
        comodel_name="l10n_br_fiscal_edi.service.message",
        inverse_name="service_id",
        string="Fiscal Service Message",
    )
