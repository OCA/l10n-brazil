# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from openerp import api, fields, models


class ResourceCalendar(models.Model):

    _inherit = 'resource.calendar'

    def quantidade_de_DSR(self, data_from, data_to):
        """Obter a quantidade de DSR em determinado período
        :param str data_from:   Data Inicial do intervalo
        :param str data_to:     Data Final do intervalo
        :return: int: quantidade de DSR no intervalo
        """
        quantidade_DSR = 0
        data_inicio = fields.Datetime.from_string(data_from)
        data_final = fields.Datetime.from_string(data_to)
        while data_inicio <= data_final:
            if data_inicio.weekday() == 6 or \
                    self.data_eh_feriado(data_inicio):
                quantidade_DSR += 1
            data_inicio += timedelta(days=1)
        return quantidade_DSR

    def desconta_feriado_como_DSR(self, data, semanas_sem_DSR):
        """
        Verificar se o feriado nao é domingo e se esta na semana que o
        funcionario faltou.
        :param datetime: data - Data do feriado
        :param list: semanas_sem_DSR - Lista com semanas que o usuário perderá
                                        DSR
        :return: boolean:   True - Feriado deve ser descontado como DSR
                            False - Nao deverá descontar feriado como DSR
        """
        return data.weekday() != 6 and data.isocalendar()[1] in semanas_sem_DSR

    @api.multi
    def get_quantity_discount_DSR(self, leaves, holidays, data_from, data_to):
        """Calcular a quantidade de DSR a serem descontados da Folha de
        pagamento de acordo com as faltas.
        A cada falta perde o(s) DSR(s) da semana
        :param resource.leaves: leaves - Faltas do funcionario
               resource.leaves: holidays - Feriados do calendario do contrato
               que esta atrelado ao funcionario
               str: data_to - Data Inicial do intervalo
               str: data_from - Data final do intervalo
        :return int : quantidade de DSR a serem descontados no intervalo
        """
        semanas_sem_DSR = []
        # percorre as faltas nao remuneradas e adiciona em uma lista a semana
        # que deve perder o DSR (Descanso semanal remunerado)
        for leave in leaves:
            if leave.holiday_status_id.descontar_DSR:
                data_inicio = fields.Datetime.from_string(leave.data_inicio)
                data_final = fields.Datetime.from_string(leave.data_fim)
                while data_inicio <= data_final:
                    # adiciona em lista o numero da semana que foi cada falta
                    semanas_sem_DSR.append(data_inicio.isocalendar()[1])
                    data_inicio += timedelta(days=1)
        quantity_DSR = len(set(semanas_sem_DSR))

        # percorre os feriados de determinado período e incrementa a quantidade
        # de DSR que deverá ser descontado, de acordo com a semana que o funcio
        # nario faltou
        for holiday in holidays:
            inicio_feriado = fields.Datetime.from_string(holiday.date_from)
            fim_feriado = fields.Datetime.from_string(holiday.date_to)

            # Se o feriado esta no intervalo passado no parametro
            if holiday.date_from >= data_from:
                if holiday.date_to <= data_to:

                    if holiday.date_from == holiday.date_to:
                        if self.desconta_feriado_como_DSR(inicio_feriado,
                                                          semanas_sem_DSR):
                            quantity_DSR += 1
                    else:
                        while fim_feriado >= inicio_feriado:
                            if self.desconta_feriado_como_DSR(inicio_feriado,
                                                              semanas_sem_DSR):
                                quantity_DSR += 1
                            inicio_feriado += timedelta(days=1)
        return quantity_DSR

    @api.multi
    def get_quantidade_dias_ferias(self, contract_id, date_from, date_to):
        """Calcular a quantidade de dias que o funcionario ficou de férias
        :param str: data_to - Data Inicial do intervalo
               str: data_from - Data final do intervalo
               int: employee_id - Id do funcionario
        :return int : quantidade de dias de ferias do funcionario
        """
        quantidade_dias_ferias = 0
        quantidade_dias_abono = 0
        holiday_status_id = \
            self.env.ref('l10n_br_hr_holiday.holiday_status_vacation')
        domain = [
            ('state', '=', 'validate'),
            ('contrato_id', '=', contract_id.id),
            ('type', '=', 'remove'),
            ('holiday_status_id', '=', holiday_status_id.id),
        ]
        ferias_holidays_ids = self.env['hr.holidays'].search(domain)
        # filtrar apenas ferias que esta dentro do periodo a ser validado
        ferias_atuais = ferias_holidays_ids.filtered(
            lambda holiday:
            (date_from <= holiday.data_inicio <= date_to) or
            (date_from <= holiday.data_fim <= date_to)
        )

        for holiday in ferias_atuais:
            data_inicio_holiday = fields.Date.from_string(holiday.data_inicio)
            data_final_holiday = fields.Date.from_string(holiday.data_fim)
            while data_inicio_holiday <= data_final_holiday:
                if date_from <= str(data_inicio_holiday) <= date_to:
                    quantidade_dias_ferias += 1
                data_inicio_holiday += timedelta(days=1)

            # Se o funcionario for vender ferias
            if holiday.sold_vacations_days:
                # data inicial do abono pecuniario sera o
                # dia anterior ao primeiro dia de férias
                data_inicial_abono = fields.Date.from_string(holiday.date_from)
                # Se a data inicial do abono estiver dentro do período que
                # esta sendo validado (quando em divisão de férias em 2+partes)
                # o abono será contabilizado. Senao o abono será contabilizado
                # na proxima parte das ferias
                if date_from == str(data_inicial_abono):
                    quantidade_dias_abono = holiday.sold_vacations_days

        return quantidade_dias_ferias, quantidade_dias_abono

    @api.multi
    def get_ultimo_dia_mes(self, mes, ano):
        """ Verificar o ultimo dia do mes referencia
        :param mes:  int - Mês de referencia
        :return: int : ultimo dia do mes
        relativedelta(months=+1, days=-1)
        """

        data_mes = datetime.strptime(str(mes) + '-' + str(ano), '%m-%Y')
        data_final = \
            data_mes + relativedelta(months=1) - relativedelta(days=1)
        return data_final

    @api.multi
    def name_get(self):
        """
        Adicionar o intervalo no nome do calendário
        """
        result = []

        for record in self:
            name = record.name
            if record.attendance_ids and \
                    record.attendance_ids[0].turno_id.horario_intervalo_ids:
                intervalo = \
                    record.attendance_ids[0].turno_id.horario_intervalo_ids[0]
                if intervalo.ini_interv and intervalo.term_interv:
                    nome_intervalo = ' (Intervalo: {} até {})'.format(
                        intervalo.ini_interv, intervalo.term_interv)
                    name = "{} {}".format(record.name, nome_intervalo)
            result.append((record.id, name))

        return result