# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from openerp import api, models, fields
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

try:
    from pybrasil import data
    from pybrasil.data import data_hora_horario_brasilia, parse_datetime, UTC
except ImportError:
    _logger.info('Cannot import pybrasil')


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    @api.multi
    def _check_date(self):
        for holiday in self:
            domain = [
                ('data_inicio', '<=', holiday.data_inicio),
                ('data_fim', '>=', holiday.data_fim),
                ('employee_id', '=', holiday.employee_id.id),
                ('id', '!=', holiday.id),
                ('tipo', '!=', 'compensacao'),
                ('type', '=', holiday.type),
                ('state', 'not in', ['cancel', 'refuse']),
                ('holiday_status_id', '=', holiday.holiday_status_id.id),
            ]
            nholidays = self.search_count(domain)
            if nholidays:
                return False
        return True

    _constraints = [
        (_check_date, 'You can not have 2 leaves that overlaps on same day!',
         ['data_inicio', 'data_fim']),
    ]

    sell_vacation = fields.Boolean(
        string=u'Sell Vacation',
        help=u'Indicates if the employee desires to sell some of its '
               u'entitled vacation days',
        default=False,
    )
    sold_vacations_days = fields.Integer(
        string=u'Sold Vacation Days',
        help=u'Number of vacation days the employee desires to sell',
        default=0,
    )
    sold_vacations_days_temp = fields.Integer(
        string=u'Sold Vacation Days',
        help=u'Number of vacation days the employee desires to sell',
        compute='_compute_days_temp',
    )
    vacations_days = fields.Integer(
        string=u'Number of vacation days',
    )
    vacations_days_temp = fields.Integer(
        string=u'Number of vacation days temp',
        compute='_compute_days_temp',
    )
    advance_13_salary = fields.Boolean(
        string=u'Advance 13th salary',
        default=False,
    )
    advance_current_salary = fields.Boolean(
        string=u'Advance Currente Salary',
        default=False,
    )
    parent_id = fields.Many2one(
        comodel_name='hr.holidays',
        string=u'Worked Period',
        ondelete='cascade',
        index=True,
    )
    child_ids = fields.One2many(
        comodel_name='hr.holidays',
        inverse_name='parent_id',
        string='Child Holidays',
    )
    controle_ferias = fields.Many2many(
        comodel_name='hr.vacation.control',
        relation='vacation_control_holidays_rel',
        column1='holiday_id',
        column2='hr_vacation_control_id',
        string=u'Controle de Férias',
    )
    controle_ferias_ids = fields.One2many(
        comodel_name='hr.vacation.control',
        string=u'Controle de Férias',
        inverse_name='hr_holiday_add_id',
    )

    saldo_disponivel = fields.Float(
        string='Saldo de dias de férias',
        related='parent_id.number_of_days_temp',
        help='Indica o total de dias que o funcionario poderá selecionar em '
             'sua programação de férias.',
    )
    saldo_final = fields.Float(
        string='Saldo final de dias de férias',
        help=u'Saldo de dias de ferias de acordo com a fórmula: \n'
             u'saldo_disponivel - dias selecionados.\n Se o resultado for '
             u'positivo, o pedido de férias é regular e ja poderá ser gozado.',
        compute='_compute_verificar_regularidade',
        compute_sudo=True,
    )
    saldo_periodo_referencia = fields.Float(
        string='Saldo do período aquisitivo',
        help=u'Indica o Saldo do período de referência.\n'
             u'Na visão de solicitação de férias, mostrar apenas os período '
             u'aquisitivos que tem saldo para gozar férias.',
        compute='compute_saldo_periodo_referencia',
        store=True,
        compute_sudo=True,
    )
    regular = fields.Boolean(
        string=u'Regular',
        compute='_compute_verificar_regularidade',
    )

    name = fields.Char(
        string='Leave Type',
        translate=True,
        compute='_compute_name_holiday',
    )

    data_inicio = fields.Date(
        string=u'Início',
    )

    data_fim = fields.Date(
        string=u'Fim',
    )

    inicio_aquisitivo = fields.Date(
        string=u'Início do Período Aquisitivo',
        compute='_compute_periodo_aquisitivo',
        store=True,
    )
    fim_aquisitivo = fields.Date(
        string=u'Fim do Período Aquisitivo',
        compute='_compute_periodo_aquisitivo',
        store=True,
    )

    @api.multi
    @api.depends('controle_ferias')
    def _compute_periodo_aquisitivo(self):
        for holiday in self:
            if holiday.controle_ferias:
                holiday.inicio_aquisitivo = \
                    holiday.controle_ferias[0].inicio_aquisitivo
                holiday.fim_aquisitivo = \
                    holiday.controle_ferias[0].fim_aquisitivo

    @api.depends('parent_id')
    def _compute_verificar_regularidade(self):
        for holiday in self:
            if not holiday.parent_id:
                continue
            dias_de_direito = holiday.parent_id.number_of_days_temp
            dias_selecionados = holiday.number_of_days_temp
            holiday.saldo_final = dias_de_direito - dias_selecionados
            holiday.regular = False
            if holiday.controle_ferias:
                if holiday.saldo_final >= 0 and holiday.date_from >= \
                        holiday.controle_ferias[0].inicio_concessivo:
                    holiday.regular = True

    @api.depends('child_ids', 'child_ids.number_of_days_temp', 'vacations_days')
    def compute_saldo_periodo_referencia(self):
        """
        Cada pedido de ferias(hr.holiday) deve ter um outro holiday como
        parent_id que indica o periodo aquisitivo daquela solicitação.
        O periodo aquisitivo (holiday parent_id tipo add) deve contabilizar
        o saldo do periodo aquisitivo, isto é, a somatoria dos holidays filhos.
        Na visao de solicitação de férias exibir apenas o periodo aquisitivo
        que tiver saldo disponivel.

        No mesmo raciocinio do periodo aquisitivo teremos outros periodos
        (hr.holidays tipo compensacao de horas) chamados de referencia que
        indicam o saldo de horas do funcionario.

        :return:
        """
        for holiday_id in self:
            eventos_gozados = 0

            solicitacoes_aprovadas = holiday_id.child_ids.filtered(
                lambda x: x.state in ['confirm', 'validate', 'validate1'])

            if holiday_id.type == 'add' and holiday_id.child_ids:

                eventos_gozados = \
                    sum(solicitacoes_aprovadas.mapped('number_of_days_temp'))

            holiday_id.saldo_periodo_referencia = \
                holiday_id.number_of_days_temp - eventos_gozados

        # for holiday_id in self:
        #
        #     solicitacoes_aprovadas = holiday_id.child_ids.filtered(
        #         lambda x: x.state in ['validate', 'validate1'])
        #
        #     #  Se o holiday for do tipo de compensacao, a contabilidade devera
        #     #  se basear na configuração de horas do holidays_status
        #     if holiday_id.type == 'add' and holiday_id.holiday_status_id.controle_horas:
        #         eventos_gozados = \
        #             sum(solicitacoes_aprovadas.mapped('horas_compensadas'))
        #
        #         horas_de_direito = \
        #             holiday_id.number_of_days_temp * \
        #             holiday_id.holiday_status_id.hours_limit
        #
        #         holiday_id.saldo_periodo_referencia = \
        #             horas_de_direito - eventos_gozados
        #
        #     #  Se o holiday NAO for do tipo compensacao, a contabilidade devera
        #     #  se basear na configuração de DIAS do holidays_status
        #     if holiday_id.type == 'add' and not holiday_id.holiday_status_id.controle_horas:
        #
        #         eventos_gozados = \
        #             sum(solicitacoes_aprovadas.mapped('number_of_days_temp'))
        #
        #         dias_de_direito = \
        #             holiday_id.number_of_days_temp * \
        #             holiday_id.holiday_status_id.days_limit
        #
        #         holiday_id.saldo_periodo_referencia = \
        #             dias_de_direito - eventos_gozados

    @api.depends('vacations_days', 'sold_vacations_days')
    def _compute_days_temp(self):
        """
        Função que seta as variaveis temporarias de férias para exibição na
        visao em formato de lista (resumo de férias)
        """
        for holiday_id in self:
            if holiday_id.type == 'remove':
                holiday_id.sold_vacations_days_temp = \
                    -holiday_id.sold_vacations_days
                holiday_id.vacations_days_temp = -holiday_id.vacations_days
            if holiday_id.type == 'add':
                holiday_id.vacations_days_temp = holiday_id.number_of_days_temp

    @api.multi
    def onchange_date_to(self, date_to, date_from, sold_vacations_days):
        result = super(HrHolidays, self).onchange_date_to(date_to, date_from)
        result['value']['vacations_days'] = \
            result['value']['number_of_days_temp']
        if sold_vacations_days > 0:
            result['value']['number_of_days_temp'] += sold_vacations_days
        return result

    @api.multi
    def onchange_date_from(self, date_to, date_from, sold_vacations_days):
        """
        On change disparado na view
        :param date_to:
        :param date_from:
        :param sold_vacations_days:
        :return:
        """
        # se for do tipo fields.Date converter para datetime para chamar rotina
        if date_to and len(date_to) == 10:
            date_to += ' 00:00:00'

        if date_from and len(date_from) == 10:
            date_from += ' 00:00:00'

        result = super(HrHolidays, self).onchange_date_to(date_to, date_from)
        result['value']['vacations_days'] = \
            result['value']['number_of_days_temp']
        if sold_vacations_days > 0:
            result['value']['number_of_days_temp'] += sold_vacations_days
        return result

    @api.onchange('sell_vacation', 'sold_vacations_days', 'vacations_days')
    def _calculate_sum_vacation_days(self):
        for record in self:
            if record.sell_vacation:
                record.number_of_days_temp = \
                    record.sold_vacations_days + record.vacations_days
            else:
                record.sold_vacations_days = 0
                record.number_of_days_temp = record.vacations_days

    @api.onchange('parent_id')
    def _compute_contract(self):
        """
        Função que configura o controle de férias no pedido de férias atual
        """
        if self.parent_id:
            self.controle_ferias = self.parent_id.controle_ferias

    @api.depends('date_from', 'date_to', 'holiday_status_id', 'employee_id',
                 'data_inicio', 'data_fim')
    def _compute_name_holiday(self):
        """
        Função que configura o nome automaticamente do holidays. Se começar e
        terminar em dias diferentes, mostre a data inicial e final do holidays,
         senão só mostra a data que acontecerá o holidays
        """
        for holiday in self:

            if holiday.employee_id:
                # Pegar apenas os dois primeiros nomes
                employee_name = filter(
                    lambda x: len(x) != 2, holiday.employee_id.name.split())
                employee_name = ' '.join(employee_name[:2])

            if holiday.data_inicio and holiday.data_fim and \
                    holiday.holiday_status_id and holiday.employee_id:
                date_from = data.formata_data(holiday.data_inicio)
                date_to = data.formata_data(holiday.data_fim)

                if date_from == date_to:
                    holiday.name = holiday.holiday_status_id.name[:30] + \
                        ' [' + employee_name + '] ' + \
                        ' (' + date_to + ')'
                else:
                    holiday.name = \
                        holiday.holiday_status_id.name[:30] + \
                        ' [' + employee_name + '] ' + \
                        ' (' + date_from + '-' + date_to + ')'

            elif holiday.holiday_status_id and holiday.employee_id:
                holiday.name = holiday.holiday_status_id.name[:30] + \
                               ' [' + employee_name + '] '

            if holiday.controle_ferias_ids and holiday.type == 'add':
                holiday.name = \
                    'Periodo Aquisitivo ' + \
                    ' (' + data.formata_data(holiday.controle_ferias_ids[0].inicio_aquisitivo) + \
                    ' - ' + \
                    data.formata_data(holiday.controle_ferias_ids[0].fim_aquisitivo) + ') '

    @api.onchange('data_inicio', 'data_fim', 'date_from', 'date_to')
    def setar_datas_core(self):
        for holiday in self:
            if holiday.data_inicio and holiday.data_fim:
                data_inicio = data_hora_horario_brasilia(
                    parse_datetime(holiday.data_inicio + ' 00:00:00'))
                holiday.date_from = str(UTC.normalize(data_inicio))[:19]
                data_fim = data_hora_horario_brasilia(
                    parse_datetime(holiday.data_fim + ' 23:59:59'))
                holiday.date_to = str(UTC.normalize(data_fim))[:19]
            elif holiday.date_from and holiday.date_to:
                holiday.data_inicio = fields.Date.from_string(
                    holiday.date_from
                )
                holiday.data_fim = fields.Date.from_string(holiday.date_to)
