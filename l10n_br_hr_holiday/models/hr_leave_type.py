# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .hr_leave import OCORRENCIA_TIPO
from odoo import fields, models

TYPE_DAY = [
    ('uteis', 'Dias úteis Consecutivos'),
    ('corridos', 'Dias corridos'),
    ('naouteis', 'Dias não úteis'),
]
TYPE = [
    ('add', 'ADD'),
    ('remove', 'Remove'),
]


class HrLeaveType(models.Model):

    _inherit = 'hr.leave.type'

    message = fields.Char(
        string="Mensagem",
    )

    days_limit = fields.Integer(
        string='Limite de Dias',
    )

    hours_limit = fields.Float(
        string='Equivalente em Horas',
    )

    type_day = fields.Selection(
        string='Tipo de Dia',
        selection=TYPE_DAY,
    )

    need_attachment = fields.Boolean(
        string='Need attachment',
    )

    payroll_discount = fields.Boolean(
        string='Descontar dia no Holerite?',
        help='Na ocorrência desse evento, será descontado em folha a '
             'quantidade de dias em afastamento.',
    )

    descontar_DSR = fields.Boolean(
        string='Descontar DSR',
        help='Descontar DSR da semana de ocorrência do evento?',
    )

    tipo_ocorrencia = fields.Selection(
        string='Tipo de Ocorrência',
        selection=OCORRENCIA_TIPO,
        default='ocorrencias',
    )

    type = fields.Selection(
        selection=OCORRENCIA_TIPO,
        string="Type",
    )

    limit = fields.Boolean(
        string='Limit',
    )
