# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from datetime import datetime, timedelta


class ResourceCalendar(models.Model):

    _inherit = 'resource.calendar'

    @api.multi
    def get_ocurrences(self, employee_id, data_from=datetime.now(),
                       data_to=datetime.now()):
        """Calcular a quantidade de faltas/ocorrencias que devem ser
        descontadas da folha de pagamento em determinado intervalo de tempo.
        :param  employee_id: Id do funcionario
                datetime data_from: Data inicial do intervalo de tempo.
                datetime data_end: Data final do intervalo
        :return dict {
                    - int faltas_remuneradas: Quantidade de faltas que devem
                    ser remuneradas dentro do intervalo passado como parâmetro
                    - int faltas_nao_remuneradas: Quantidade de faltas que NAO
                    serao remuneradas. (Descontadas da folha de pagamento)
        }
        """
        faltas = {
            'faltas_remuneradas': [],
            'faltas_nao_remuneradas': [],
        }
        domain = [
            ('state', '=', 'validate'),
            ('employee_id', '=', employee_id),
            ('type', '=', 'remove'),
            ('date_from', '>=', data_from),
            ('date_to', '<=', data_to),
        ]
        holidays_ids = self.env['hr.holidays'].search(domain)

        for leave in holidays_ids:
            if leave.payroll_discount:
                faltas['faltas_nao_remuneradas'].append(leave)
            else:
                faltas['faltas_remuneradas'].append(leave)
        return faltas

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
    def get_quantity_discount_DSR(self, leaves):
        """Calcular a quantidade de DSR a serem descontados da Folha de
        pagamento de acordo com as faltas.
        A cada falta perde o(s) DSR(s) da semana
        :param resource.leaves : Faltas
        :return int : quantidade de DSR a serem descontados
        """
        DSR_perdido = []
        # percorre as faltas nao remuneradas
        for leave in leaves:
            data_inicio = fields.Datetime.from_string(leave.date_from)
            data_final = fields.Datetime.from_string(leave.date_to)
            while data_inicio <= data_final:
                # adiciona em uma lista o numero da semana que foi cada falta
                DSR_perdido.append(fields.Datetime.from_string(leave.date_to).
                                   isocalendar()[1])
                data_inicio += timedelta(days=1)

        return len(set(DSR_perdido))
