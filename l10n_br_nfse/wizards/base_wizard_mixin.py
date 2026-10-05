# Copyright 2026 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BaseWizardMixin(models.AbstractModel):
    """Expose the RPS number in the shared fiscal wizards."""

    _inherit = "l10n_br_fiscal.base.wizard.mixin"

    rps_number = fields.Char()

    def _document_fields(self):
        return super()._document_fields() + ["rps_number"]
