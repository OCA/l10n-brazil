# -*- coding: utf-8 -*-
# Copyright 2016 Luis Felipe Mileo - KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _


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
            worked_days = self.env['resource.calendar'].retorna_num_dias_uteis(
                fields.Datetime.from_string(date_from),
                fields.Datetime.from_string(date_to),
            )
            attendances = {
                 'name': u"Dias Úteis",
                 'sequence': 1,
                 'code': 'WORK100',
                 'number_of_days': worked_days,
                 'number_of_hours': 0.0,
                 'contract_id': contract_id.id,
            }
            result += [attendances]
        return result
