# Copyright (C) 2022  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class Service(models.Model):
    """Catalog of the SEFAZ electronic document webservices.

    The authorization, status, inutilizacao, distribution and event
    reception webservices (NFeAutorizacao, NFeRecepcaoEvento...) a
    fiscal document type supports. This is only the registry of the
    services: the actual SOAP transmission is encapsulated by the
    fiscal client library (nfelib).
    """

    _name = "l10n_br_fiscal_edi.service"
    _inherit = "l10n_br_fiscal.data.abstract"
    _description = "Fiscal Document Service"

    description = fields.Text()

    document_type_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.document.type",
        string="Document Types",
    )
