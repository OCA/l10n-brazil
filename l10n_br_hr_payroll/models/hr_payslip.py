# -*- coding: utf-8 -*-
# Copyright 2016 Luis Felipe Mileo - KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class HrPayslip(models.Model):

    _inherit = 'hr.payslip'

    @api.multi
    def get_worked_day_lines(self, date_from, date_to):
        """
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should
        be applied for the given contract between date_from and date_to
        """
        result = []
        for contract_id in self:

            # get dias uteis
            worked_days = self.env['resource.calendar'].get_dias_base(
                fields.Datetime.from_string(date_from),
                fields.Datetime.from_string(date_to),
            )
            attendances = {
                'name': u"Dias Base",
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': worked_days,
                'number_of_hours': 0.0,
                'contract_id': contract_id.id,
            }
            result += [attendances]

            # get faltas
            leaves = {}
            hr_contract = self.env['hr.contract'].browse(contract_id.id)
            leaves = self.env['resource.calendar'].get_ocurrences(
                hr_contract.employee_id.id, date_from, date_to)
            if leaves.get('faltas_nao_remuneradas'):
                attendances = {
                    'name': u"Faltas Não remuneradas",
                    'sequence': 2,
                    'code': 'FNR',
                    'number_of_days': -len(leaves['faltas_nao_remuneradas']),
                    'number_of_hours': 0.0,
                    'contract_id': contract_id.id,
                }
                result += [attendances]

            # get discount DSR
            quantity_DSR_discount = self.env['resource.calendar'].\
                get_quantity_discount_DSR(leaves['faltas_nao_remuneradas'],
                                          hr_contract.working_hours.leave_ids,
                                          date_from, date_to)
            if leaves.get('faltas_nao_remuneradas'):
                ref_quantity_DSR_discount = {
                    'name': u"DSR a serem descontados",
                    'sequence': 3,
                    'code': 'DSR',
                    'number_of_days': -quantity_DSR_discount,
                    'number_of_hours': 0.0,
                    'contract_id': contract_id.id,
                }
                result += [ref_quantity_DSR_discount]
            return result
