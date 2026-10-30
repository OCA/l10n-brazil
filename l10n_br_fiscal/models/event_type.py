# Copyright (C) 2025  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class EventType(models.Model):
    """Catalog of fiscal document event types (tpEvento).

    SEFAZ event types (NT 2018.001 for the NF-e, CT-e and MDF-e event
    manuals) such as 110110 (Carta de Correcao), 110111 (Cancelamento)
    or the recipient manifestation events 2102xx. This is generic fiscal
    master data: the NFe/CTe/MDFe modules provide the actual records and
    the EDI layer (l10n_br_fiscal_edi) logs the transmitted events.
    """

    _name = "l10n_br_fiscal.event.type"
    _inherit = "l10n_br_fiscal.data.abstract"
    _description = "Fiscal Document Event Type"

    description = fields.Text()

    actor = fields.Selection(
        selection=[
            ("issuer", "Registered by the Issuer"),
            ("recipient", "Registered by the Recipient"),
            ("fisco", "Registered by the Tax Authorities"),
            ("propagation", "Propagated from Other Documents"),
            ("other", "Other"),
        ],
        help="Who registers the event at the tax authorities, "
        "as grouped in the SEFAZ event technical notes.",
    )

    document_type_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.document.type",
        string="Document Types",
        help="Fiscal document types (NF-e, CT-e, MDF-e...) this event "
        "type applies to.",
    )
