# Copyright (C) 2026  Engenere - Antônio S. Pereira Neto <neto@engenere.one>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models

from odoo.addons.l10n_br_fiscal.constants.fiscal import DOCUMENT_STATE_OPEN

from ..constants.fiscal import (
    DOCUMENT_STATE_AUTHORIZED,
    DOCUMENT_STATE_DENIED,
    DOCUMENT_STATE_REJECTED,
    DOCUMENT_STATE_SENDING,
)


class Operation(models.Model):
    _inherit = "l10n_br_fiscal.operation"

    def _dashboard_2confirm_states(self):
        """With EDI installed, 'open' means confirmed but not transmitted
        yet, so it belongs to the 'to confirm' bucket together with the
        transmission retry states."""
        return super()._dashboard_2confirm_states() + [
            DOCUMENT_STATE_OPEN,
            DOCUMENT_STATE_SENDING,
            DOCUMENT_STATE_REJECTED,
        ]

    def _dashboard_authorized_states(self):
        """Only documents actually authorized by the tax authority."""
        return [DOCUMENT_STATE_AUTHORIZED]

    def _dashboard_cancelled_states(self):
        return super()._dashboard_cancelled_states() + [DOCUMENT_STATE_DENIED]
