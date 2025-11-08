from odoo import fields, models


class NfeRecipientManifestationEvent(models.Model):
    _inherit = "l10n_br_nfe.recipient_manifestation_event"

    nfe_dfe_bundle_id = fields.Many2one(
        string="DF-e", comodel_name="l10n_br_fiscal.nfe_dfe_bundle"
    )
