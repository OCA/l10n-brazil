# Copyright (C) 2025  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class DocumentType(models.Model):
    _inherit = "l10n_br_fiscal.document.type"

    service_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal_edi.service",
        string="Document Service",
    )

    event_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal_edi.event",
        string="Document Event",
    )
