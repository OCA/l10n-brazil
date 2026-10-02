# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import DOCUMENT_STATE_OPEN
from odoo.addons.l10n_br_fiscal_edi.constants.fiscal import (
    DOCUMENT_STATE_REJECTED,
    DOCUMENT_STATE_SENDING,
)
from odoo.addons.queue_job.job import identity_exact

_logger = logging.getLogger(__name__)

# States from which the action_send transition of the state machine can
# start a transmission: SENDING is included because action_send also resends
# or consults the receipt of a document still waiting for processing
SENDABLE_STATES = (
    DOCUMENT_STATE_OPEN,
    DOCUMENT_STATE_REJECTED,
    DOCUMENT_STATE_SENDING,
)


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    def _queue_document_send_later(self):
        """Whether this document must be transmitted through the job queue."""
        self.ensure_one()
        return self.fiscal_operation_id.queue_document_send == "with_delay"

    def action_document_send(self):
        """Split documents between synchronous and queued transmission.

        Documents whose fiscal operation is configured as ``with_delay`` keep
        their state and get a queue_job that fires the ``action_send``
        transition later, off the HTTP worker. The remaining documents go
        through the state machine right away, as in ``l10n_br_fiscal_edi``.
        """
        if self.env.context.get("l10n_br_fiscal_queue_send_now"):
            return super().action_document_send()

        to_delay = self.filtered(lambda d: d._queue_document_send_later())
        for document in to_delay:
            _logger.info(
                "Enqueuing fiscal document %s for asynchronous transmission",
                document.id,
            )
            document.with_delay(
                channel="root.edocument",
                identity_key=identity_exact,
                description=_("Transmit fiscal document %s to SEFAZ")
                % document.display_name,
            )._job_document_send()

        to_send_now = self - to_delay
        if to_send_now:
            return super(FiscalDocument, to_send_now).action_document_send()
        return True

    def _job_document_send(self):
        """Runs inside the queue_job worker: perform the real transmission."""
        self.ensure_one()
        if self.state_edoc not in SENDABLE_STATES:
            # sent, cancelled or set back to draft while the job waited
            _logger.info(
                "Fiscal document %s is in state %s, nothing to transmit",
                self.id,
                self.state_edoc,
            )
            return False
        return self.with_context(
            l10n_br_fiscal_queue_send_now=True
        ).action_document_send()
