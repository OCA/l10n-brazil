# -*- coding: utf-8 -*-
#
# Copyright 2016 KMEE - Luis Felipe Miléo <mileo@kmee.com.br>
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# Copyright 2017 KMEE - Aristides Caldeira <aristides.caldeira@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#

import logging
from odoo import api, fields, models, _
from odoo.exceptions import AccessError
from datetime import datetime, timedelta
from odoo import tools

_logger = logging.getLogger(__name__)


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    def _get_brazilian_calendar(self):
        br_calendar_id = self.env['ir.config_parameter'].search(
            [('key', '=', 'l10n_br_resource.br_calendar')]).value

        if not br_calendar_id:
            raise AccessError(
                u"Calendário Brasileiro não encontrado, favor importa-lo "
                u"manualmente"
            )
            #  TODO: Importar o calendário
        return self.browse(int(br_calendar_id))

    def _compute_recursive_leaves(self, calendar):
        res = self.env['resource.calendar.leaves']
        res |= self.env['resource.calendar.leaves'].search([
            ('calendar_id', '=', calendar.id)
        ])
        if calendar.parent_id:
            res |= self._compute_recursive_leaves(calendar.parent_id)
        return res

    @api.multi
    @api.depends('parent_id')
    def _compute_leave_ids(self):
        for calendar in self:
            calendar.leave_ids = self._compute_recursive_leaves(calendar)

    parent_id = fields.Many2one(
        comodel_name='resource.calendar',
        string='Parent Calendar',
        ondelete='restrict',
        index=True)
    child_ids = fields.One2many(
        'resource.calendar',
        'parent_id',
        string='Child Calendar')
    _parent_store = True
    parent_left = fields.Integer(index=True)
    parent_right = fields.Integer(index=True)

    country_id = fields.Many2one('res.country', u'País')
    state_id = fields.Many2one(
        'res.country.state', u'Estado',
        domain="[('country_id','=',country_id)]")
    municipio_id = fields.Many2one(
        comodel_name='sped.municipio',
        string=u'Municipio',
        domain="[('estado_id.state_id', '=', state_id)]"
    )
    leave_ids = fields.Many2many(
        comodel_name='resource.calendar.leaves',
        compute='_compute_leave_ids'
    )

    @api.constrains('parent_id')
    def _check_hierarchy(self):
        if not self._check_recursion():
            raise models.ValidationError(_(
                'Error! You cannot create recursive calendars.'))

    @api.multi
    def get_leave_intervals(self, resource_id=None, start_datetime=None,
                            end_datetime=None):
        """Get the leaves of the calendar. Leaves can be filtered on the
        resource, the start datetime or the end datetime.

        :param int resource_id: the id of the resource to take into account
                                when computing the leaves. If not set,
                                only general leaves are computed.
                                If set, generic and specific leaves
                                are computed.
        :param datetime start_datetime: if provided, do not take into
                                        account leaves ending before
                                        this date.
        :param datetime end_datetime: if provided, do not take into
                                        account leaves beginning
                                        after this date.

        :return list leaves: list of tuples (start_datetime, end_datetime) of
                             leave intervals
        """
        leaves = []
        for leave in self.leave_ids:
            if leave.resource_id and resource_id:
                if leave.resource_id and not resource_id == leave. \
                        resource_id.id:
                    continue
            elif leave.resource_id and not resource_id:
                continue
            date_from = datetime.strptime(
                leave.date_from, tools.DEFAULT_SERVER_DATETIME_FORMAT
            )
            if end_datetime and date_from > end_datetime:
                continue
            date_to = datetime.strptime(
                leave.date_to, tools.DEFAULT_SERVER_DATETIME_FORMAT
            )
            if start_datetime and date_to < start_datetime:
                continue
            leaves.append(leave)
        return leaves

    @api.multi
    def data_eh_feriado(self, data_referencia=datetime.now()):
        """Verificar se uma data é feriado.
        :param datetime data_referencia: Se nenhuma data referencia for passada
                                    verifique se hoje eh feriado no calendario
                                    corrente.
                                    Se a data referencia for passada, verifique
                                    se a data esta dentro de algum leave do
                                    calendario corrente
                                    date_start <= data_referencia <= data_end

        :return boolean True se a data referencia for feriado
                        False se a data referencia nao for feriado
        """
        if not self.leave_ids:
            self = self.with_context(self._context)._get_brazilian_calendar()
        for leave in self.leave_ids:
            if leave.date_from <= data_referencia.strftime(
                    "%Y-%m-%d %H:%M:%S"):
                if leave.date_to >= data_referencia. \
                        strftime("%Y-%m-%d %H:%M:%S"):
                    if leave.leave_kind in ('F', 'B'):
                        return True
        return False

    @api.multi
    def data_eh_dia_util(self, data=datetime.now()):
        """Verificar se data é dia util.
        :param datetime data: Se nenhuma data referencia for passada
                              verifique o dia de hoje.
        :return boolean True: Se for dia útil
                        False: Se Não for dia útil
        """
        return not self.data_eh_feriado(data) and data.weekday() <= 4 or False

    @api.multi
    def data_eh_dia_util_bancario(self, data=datetime.now()):
        """Verificar se data é dia util.
        :param datetime data: Se nenhuma data referencia for passada
                              verifique o dia de hoje.
        :return boolean True: Se for dia útil
                        False: Se Não for dia útil
        """
        if data.weekday() > 4:
            return False
        elif self.data_eh_feriado_bancario(data):
            return False
        return True

    @api.multi
    def quantidade_dias_uteis(
            self, data_inicio=datetime.now(), data_fim=datetime.now()):
        """Calcular a quantidade de dias úteis em determinado período.
        :param datetime data_inicio: Se nenhuma data referencia for passada
                                   verifique o dia de hoje.
        :param datetime data_fim: Se nenhuma data referencia for passada
                                   verifique o dia de hoje.
        :return int: Quantidade de dias úteis
        """
        dias_uteis = 0
        while data_inicio <= data_fim:
            if self.data_eh_dia_util(data_inicio):
                dias_uteis += 1
            data_inicio += timedelta(days=1)

        return dias_uteis

    @api.multi
    def proximo_dia_util(self, data_referencia=datetime.now()):
        """Retornar o próximo dia util.
        :param datetime data_referencia: Se nenhuma data referencia for passada
                                   verifique se amanha é dia útil.
        :return datetime Proximo dia util apartir da data referencia
        """
        while data_referencia:
            if self.data_eh_dia_util(data_referencia):
                return data_referencia
            data_referencia += timedelta(days=1)

    @api.multi
    def proximo_dia_util_bancario(self, data_referencia=datetime.now()):
        """Retornar o próximo dia util.
        :param datetime data_referencia: Se nenhuma data referencia for passada
                                   verifique se amanha é dia útil.
        :return datetime Proximo dia util apartir da data referencia
        """
        if self.data_eh_dia_util_bancario(data_referencia):
            return data_referencia
        data_referencia += timedelta(days=1)
        return self.proximo_dia_util_bancario(data_referencia)

    @api.multi
    def get_dias_base(self, data_from=datetime.now(), data_to=datetime.now()):
        """Calcular a quantidade de dias que devem ser remunerados em
        determinado intervalo de tempo.
        :param datetime data_from: Data inicial do intervalo de tempo.
               datetime data_end: Data final do intervalo
        :return int : quantidade de dias que devem ser remunerada
       """
        quantidade_dias = (data_to - data_from).days + 1
        if quantidade_dias > 30:
            return 30
        else:
            return quantidade_dias

    @api.multi
    def data_eh_feriado_bancario(self, data_referencia=datetime.now()):
        """Verificar se uma data é feriado bancário.
        :param datetime data_referencia: Se nenhuma data referencia for passada
                                    verifique se hoje é feriado bancário.
                                    Se a data referencia for passada, verifique
                                    se a data esta dentro de algum leave
                                    date_start <= data_referencia <= data_end

        :return int leaves_count: +1 se for feriado bancário
                                   0 se a data nao for feriado bancário
        """
        if not self.leave_ids:
            self = self.with_context(self._context)._get_brazilian_calendar()
        if self.leave_ids.filtered(
                lambda record: data_referencia.strftime("%Y-%m-%d 00:00:00") <=
                record.date_from <=
                data_referencia.strftime("%Y-%m-%d 23:59:59") and
                record.leave_kind == 'B'):
            return True
        return False

    @api.multi
    def data_eh_feriado_emendado(self, data_referencia=datetime.now()):
        """Verificar se uma data é feriado emendado.
        :param datetime data_referencia: Se nenhuma data referencia for passada
                                   verifique se hoje é feriado emendado.
                                   Se a data referencia for passada, verifique
                                   se a data esta dentro de algum leave
                                   date_start <= data_referencia <= data_end

        :return retorna True ou False
        """
        dia_antes = data_referencia - timedelta(days=2)
        dia_depois = data_referencia + timedelta(days=2)

        dia_antes_eh_util = \
            True if dia_antes.weekday() > 5 or self.data_eh_feriado(
                dia_antes) else False
        dia_depois_eh_util = \
            True if dia_depois.weekday() > 4 or self.data_eh_feriado(
                dia_depois) else False

        return dia_antes_eh_util or dia_depois_eh_util
