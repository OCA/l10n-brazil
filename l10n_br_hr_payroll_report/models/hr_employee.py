# -*- coding: utf-8 -*-

from openerp import models, fields, api
import logging

_logger = logging.getLogger(__name__)

try:
    from pybrasil import data
except ImportError:
    _logger.info('Cannot import pybrasil')


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    birthday_fmt = fields.Char(
        string=u'Data de Nascimento',
        default='0',
        compute='_compute_birthday_formatado'
    )

    @api.depends('birthday')
    def _compute_birthday_formatado(self):
        for empregado in self:
            if empregado.birthday:
                empregado.birthday_fmt = data.formata_data(empregado.birthday)

    @api.multi
    def open_ficha_registro(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ficha Registro',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'wizard.l10n_br_hr_employee.ficha_registro',
            'context': {'employee_id': self.id}
        }
