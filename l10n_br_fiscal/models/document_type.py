# Copyright (C) 2009  Renato Lima - Akretion <renato.lima@akretion.com.br>
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models

from ..constants.fiscal import DOCUMENT_TYPE


class DocumentType(models.Model):
    _name = "l10n_br_fiscal.document.type"
    _description = "Fiscal Document Type"
    _inheirt = "l10n_br_fiscal.data.abstract"

    code = fields.Char(
        size=8)

    name = fields.Char(
        size=128)

    electronic = fields.Boolean(
        string="Is Electronic?")

    type = fields.Selection(
        selection=DOCUMENT_TYPE,
        string="Document Type",
        required=True)

    document_serie_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document.serie",
        inverse_name="document_type_id",
        string="Document Series")
