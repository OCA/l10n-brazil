# Copyright 2018 KMEE INFORMATICA LTDA
#   Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

import logging

from odoo import models, _
from odoo.addons.queue_job.job import job

_logger = logging.getLogger(__name__)


class SubsequentDocument(models.Model):
    _inherit = 'l10n_br_fiscal.subsequent.document'

    @job
    def _gera_documento_subsequente_job(self):
        self._gera_documento_subsequente()

    def gera_documento_subsequente(self):
        _logger.info(_('Gerando documento fiscal %s', self.ids))

        if self.operacao_subsequente_id.gerar_documento == 'now':
            _logger.info(_('Gerando documento fiscal agora: %s',
                         self.documento_origem_id.ids))
            self._gera_documento_subsequente_job()
        else:
            _logger.info(_('Gerando documento fiscal depois: %s',
                         self.documento_origem_id.ids))
            self.with_delay()._gera_documento_subsequente_job()
