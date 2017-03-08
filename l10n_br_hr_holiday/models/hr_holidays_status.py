# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.l10n_br_hr_holiday.models.hr_holidays \
    import OCORRENCIA_TIPO
from openerp import fields, models

TYPE_DAY = [
    ('uteis', u'Dias úteis Consecutivos'),
    ('corridos', u'Dias corridos'),
]


class HrHolidaysStatus(models.Model):

    _inherit = 'hr.holidays.status'

    message = fields.Char(
        string=u"Mensagem",
    )

    days_limit = fields.Integer(
        string=u'Limite de Dias',
    )

    hours_limit = fields.Integer(
        string=u'Limite de Horas',
    )

    type_day = fields.Selection(
        string=u'Tipo de Dia',
        selection=TYPE_DAY,
    )

    need_attachment = fields.Boolean(
        string=u'Need attachment',
    )

    payroll_discount = fields.Boolean(
        string=u'Payroll Discount',
    )

    tipo = fields.Selection(
        string=u'Tipo',
        selection=OCORRENCIA_TIPO,
        default='ocorrencias',
    )
