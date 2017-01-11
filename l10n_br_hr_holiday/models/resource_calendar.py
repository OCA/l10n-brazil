# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from datetime import datetime, timedelta


class ResourceCalendar(models.Model):

    _inherit = 'resource.calendar'

    @api.multi
    def get_ocurrences(self, employee_id, data_from, data_to):
        """Calcular a quantidade de faltas/ocorrencias que devem ser
        descontadas da folha de pagamento em determinado intervalo de tempo.
        :param  employee_id: Id do funcionario
                str data_from: Data inicial do intervalo de tempo.
                str data_end: Data final do intervalo
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
