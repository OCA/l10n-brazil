# -*- coding: utf-8 -*-
# Copyright 2016 Luis Felipe Mileo - KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class HrPayslip(models.Model):

    _inherit = 'hr.payslip'

    def get_attendances(self, nome, sequence, code, number_of_days,
                        number_of_hours, contract_id):
        attendance = {
                'name': nome,
                'sequence': sequence,
                'code': code,
                'number_of_days': number_of_days,
                'number_of_hours': number_of_hours,
                'contract_id': contract_id.id,
        }
        return attendance

    @api.multi
    def get_worked_day_lines(self, date_from, date_to):
        """
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should
        be applied for the given contract between date_from and date_to
        """
        result = []
        for contract_id in self:

            # get dias Base para cálculo do mês
            worked_days = self.env['resource.calendar'].get_dias_base(
                fields.Datetime.from_string(date_from),
                fields.Datetime.from_string(date_to))
            result += [self.get_attendances(u'Dias Base', 1, u'WORK100',
                                            worked_days, 0.0, contract_id)]

            # get faltas
            leaves = {}
            hr_contract = self.env['hr.contract'].browse(contract_id.id)
            leaves = self.env['resource.calendar'].get_ocurrences(
                hr_contract.employee_id.id, date_from, date_to)
            if leaves.get('faltas_nao_remuneradas'):
                quantity_leaves = -len(leaves['faltas_nao_remuneradas'])
                result += [self.get_attendances(u'Faltas Não remuneradas', 2,
                                                u'FNR', quantity_leaves,
                                                0.0, contract_id)]

            # get discount DSR
            quantity_DSR_discount = -self.env['resource.calendar'].\
                get_quantity_discount_DSR(leaves['faltas_nao_remuneradas'],
                                          hr_contract.working_hours.leave_ids,
                                          date_from, date_to)
            if leaves.get('faltas_nao_remuneradas'):
                result += [self.get_attendances(u'DSR a serem descontados', 3,
                                                u'DSR', quantity_DSR_discount,
                                                0.0, contract_id)]
            return result
