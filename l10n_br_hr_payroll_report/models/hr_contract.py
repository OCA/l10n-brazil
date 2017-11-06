# -*- coding: utf-8 -*-

from openerp import models, fields, api
import logging

_logger = logging.getLogger(__name__)

try:
    from pybrasil import data
except ImportError:
    _logger.info('Cannot import pybrasil')


class HrContract(models.Model):
    _inherit = 'hr.contract'

    aviso_previo_fmt = fields.Char(
        string=u'Data do aviso prévio',
        default='0',
        compute='_compute_datas_formatadas'
    )

    data_afastamento_fmt = fields.Char(
        string=u'Data do aviso prévio',
        default='0',
        compute='_compute_datas_formatadas'
    )

    @api.depends('notice_of_termination_date', 'resignation_date')
    def _compute_datas_formatadas(self):
        for contrato in self:
            if contrato.notice_of_termination_date:
                contrato.aviso_previo_fmt = data.formata_data(
                    contrato.notice_of_termination_date
                )
            if contrato.resignation_date:
                contrato.data_afastamento_fmt = data.formata_data(
                    contrato.resignation_date
                )
