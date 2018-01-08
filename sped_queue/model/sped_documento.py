# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models, fields, api
from odoo.addons.queue_job.job import job

_logger = logging.getLogger(__name__)


class SpedDocumento(models.Model):
    _inherit = 'sped.documento'

    @api.multi
    @job
    def _envia_documento_job(self):
        for record in self:
            record._envia_documento()

    @api.multi
    def envia_documento(self):
        _logger.info('Enviando documento fiscal %s', self.ids)

        enviar_agora = self.filtered(
            lambda documento:
                documento.operacao_id.momento_envio_documento == 'now'
        )
        enviar_depois = self - enviar_agora
        if enviar_agora:
            _logger.info('Enviando documento fiscal agora: %s',
                         enviar_agora.ids)
            enviar_agora._envia_documento_job()
        if enviar_depois:
            _logger.info('Enviando documento fiscal depois: %s',
                         enviar_depois.ids)
            enviar_depois.with_delay()._envia_documento_job()
