# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from datetime import datetime, timedelta


class ResourceCalendar(models.Model):

    _inherit = 'resource.calendar'

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
            data_inicio = fields.Datetime.from_string(leave.date_from)
            data_final = fields.Datetime.from_string(leave.date_to)
            while data_inicio <= data_final:
                # adiciona em uma lista o numero da semana que foi cada falta
                semanas_sem_DSR.append(fields.Datetime.from_string(
                    leave.date_to).isocalendar()[1])
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
