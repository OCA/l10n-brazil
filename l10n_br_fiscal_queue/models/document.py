# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, models

from odoo.addons.queue_job.job import identity_exact

_logger = logging.getLogger(__name__)


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    def _queue_document_send_later(self):
        """Whether this document must be transmitted through the job queue."""
        self.ensure_one()
        return self.fiscal_operation_id.queue_document_send == "with_delay"

    def _document_send(self):
        """Split documents between synchronous and queued transmission.

        Documents whose fiscal operation is configured as ``with_delay`` are
        transmitted to SEFAZ from a queue_job worker (``_job_document_send``),
        off the HTTP worker that would otherwise block for the whole SEFAZ
        round trip. The remaining documents keep the standard synchronous
        behaviour of ``l10n_br_fiscal_edi``.

        ``_document_send`` is overridden (instead of the concrete
        ``_eletronic_document_send`` implemented by l10n_br_nfe and siblings)
        precisely because no transmission module overrides ``_document_send``:
        this keeps a clean, single-hop MRO and lets the job re-enter the
        regular flow through ``super()`` regardless of which e-document module
        is installed.
        """
        to_delay = self.filtered(lambda d: d._queue_document_send_later())
        to_send_now = self - to_delay

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

        if to_send_now:
            return super(FiscalDocument, to_send_now)._document_send()
        return True

    def _job_document_send(self):
        """Runs inside the queue_job worker: perform the real transmission.

        Calls ``super()._document_send()`` with this class explicit in the MRO
        so the concrete transmission (l10n_br_nfe, l10n_br_nfce, ...) runs
        synchronously here, in the job, instead of re-entering the split above.
        """
        self.ensure_one()
        return super()._document_send()
