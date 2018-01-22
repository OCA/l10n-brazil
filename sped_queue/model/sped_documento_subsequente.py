# -*- coding: utf-8 -*-
#
# Copyright 2018 KMEE INFORMATICA LTDA
#   Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, _
from odoo.addons.queue_job.job import job
import logging
_logger = logging.getLogger(__name__)


class SpedDocumentoSubsequente(models.Model):
    _inherit = b'sped.documento.subsequente'

    @api.multi
    @job
    def _gera_documento_subsequente_job(self):
        self._gera_documento_subsequente()

    @api.multi
    def gera_documento_subsequente(self):
        _logger.info('Gerando documento fiscal %s', self.ids)

        if self.operacao_subsequente_id.gerar_documento == 'now':
            _logger.info('Gerando documento fiscal agora: %s',
                         self.documento_origem_id.ids)
            self._gera_documento_subsequente_job()
        else:
            _logger.info('Gerando documento fiscal depois: %s',
                         self.documento_origem_id.ids)
            self.with_delay()._gera_documento_subsequente_job()
