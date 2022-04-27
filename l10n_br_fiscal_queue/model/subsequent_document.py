# Copyright 2018 KMEE INFORMATICA LTDA
#   Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import logging

from odoo import _, models

_logger = logging.getLogger(__name__)


class SubsequentDocument(models.Model):
    _inherit = "l10n_br_fiscal.subsequent.document"

    def _generate_subsequent_document_job(self):
        self._generate_subsequent_document()

    def generate_subsequent_document(self):
        _logger.info(_("Generating fiscal document %s", self.ids))

        if self.operacao_subsequente_id.queue_document_send == "send_now":
            _logger.info(
                _("Generating fiscal document now: %s", self.documento_origem_id.ids)
            )
            self._generate_subsequent_document_job()
        else:
            _logger.info(
                _("Generating fiscal document later: %s", self.documento_origem_id.ids)
            )
            self.with_delay()._generate_subsequent_document_job()
