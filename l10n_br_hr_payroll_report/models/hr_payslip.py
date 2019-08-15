# -*- coding: utf-8 -*-

from openerp import models, fields, api
import logging

_logger = logging.getLogger(__name__)

try:
    from pybrasil import data
except ImportError:
    _logger.info('Cannot import pybrasil')


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    data_aviso_previo_fmt = fields.Char(
        string=u'Data do aviso prévio',
        default=' / / ',
        compute='_compute_data_aviso_previo',
        store=True,
    )

    data_afastamento_fmt = fields.Char(
        string=u'Data do aviso prévio',
        default=' / / ',
        compute='_compute_data_afastamento',
        store=True,
    )

    @api.depends('dias_aviso_previo_trabalhados')
    def _compute_data_aviso_previo(self):
        for payslip_id in self:
            if payslip_id.dias_aviso_previo_trabalhados:
                payslip_id.data_aviso_previo_fmt = \
                    data.formata_data(payslip_id.dias_aviso_previo_trabalhados) or ' '
            else:
                payslip_id.data_aviso_previo_fmt = ' / / '

    @api.depends('data_afastamento')
    def _compute_data_afastamento(self):
        for payslip_id in self:
            if payslip_id.data_afastamento:
                payslip_id.data_afastamento_fmt = \
                    data.formata_data(payslip_id.data_afastamento)
            else:
                payslip_id.data_aviso_previo_fmt = ' / / '

    @api.model
    def remove_old_payslip_reports(self):
        try:
            rep1_id = self.env.ref('hr_payroll.action_report_payslip')
            if rep1_id:
                rep1_id.unlink()
        except:
            pass
        try:
            rep2_id = self.env.ref('hr_payroll.payslip_details_report')
            if rep2_id:
                rep2_id.unlink()
        except:
            pass
