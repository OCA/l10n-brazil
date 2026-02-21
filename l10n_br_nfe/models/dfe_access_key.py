# Copyright (C) 2025-Today - Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class DFeAccessKey(models.Model):
    _inherit = "l10n_br_fiscal.dfe_access_key"

    nfe_recipient_manifestation_event_ids = fields.One2many(
        comodel_name="l10n_br_nfe.recipient_manifestation_event",
        inverse_name="dfe_access_key_id",
        string="Manifestações do Destinatário Importadas",
    )
