# -*- encoding: utf-8 -*-
###############################################################################
#
#    Brazillian Human Resources Payroll module for OpenERP
#    Copyright (C) 2014 KMEE (http://www.kmee.com.br)
#    @author Matheus Felix <matheus.felix@kmee.com.br>
#            Rafael da Silva Lima <rafael.lima@kmee.com.br>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp.osv import orm, fields
import openerp.addons.decimal_precision as dp
import time
from decimal import Decimal, ROUND_DOWN


class HrContract(orm.Model):

    _inherit = 'hr.contract'

    def _get_wage_ir(self, cr, uid, ids, fields, arg, context=None):
        res = {}
        obj_employee = self.pool.get('hr.employee')
        employee_ids = obj_employee.search(
            cr, uid, [
                ('contract_ids.id', '=', ids[0])])
        employees = obj_employee.browse(cr, uid, employee_ids, context=context)
        for employee in employees:
            for contract in employee.contract_ids:
                if employee_ids:
                    INSS = (-482.93 if ((contract.wage) >= 4390.25)
                            else -((contract.wage) * 0.11)
                            if ((contract.wage) >= 2195.13) and
                            ((contract.wage) <= 4390.24)
                            else -((contract.wage) * 0.09)
                            if ((contract.wage) >= 1317.08) and
                            ((contract.wage) <= 2195.12)
                            else -((contract.wage) * 0.08))
                    lane = (contract.wage - employee.n_dependent + INSS)
                    first_lane = (-(0.275 * (lane) - 826.15))
                    l1 = Decimal(str(first_lane))
                    lane1 = l1.quantize(Decimal('1.10'), rounding=ROUND_DOWN)
                    option_one = float(lane1)
                    second_lane = (-(0.225 * (lane) - 602.96))
                    l2 = Decimal(str(second_lane))
                    lane2 = l2.quantize(Decimal('1.10'), rounding=ROUND_DOWN)
                    option_two = float(lane2)
                    third_lane = (-(0.150 * (lane) - 335.03))
                    l3 = Decimal(str(third_lane))
                    lane3 = l3.quantize(Decimal('1.10'), rounding=ROUND_DOWN)
                    option_three = float(lane3)
                    fourth_lane = (-(0.075 * (lane) - 134.08))
                    l4 = Decimal(str(fourth_lane))
                    lane4 = l4.quantize(Decimal('1.10'), rounding=ROUND_DOWN)
                    option_four = float(lane4)
                    if (lane >= 4463.81):
                        res[ids[0]] = option_one
                        return res
                    elif (lane <= 4463.80) and (lane >= 3572.44):
                        res[ids[0]] = option_two
                        return res
                    elif (lane <= 3572.43) and (lane >= 2679.30):
                        res[ids[0]] = option_three
                        return res
                    elif (lane <= 2679.29) and (lane >= 1787.78):
                        res[ids[0]] = option_four
                        return res
                    else:
                        return 0

    def _get_worked_days(self, cr, uid, ids, fields, arg, context=None):
        res = {}

        obj_worked_days = self.pool.get('hr.payslip.worked_days')
        worked_ids = obj_worked_days.search(
            cr, uid, [
                ('contract_id', '=', ids[0])])
        if worked_ids:
            worked = obj_worked_days.browse(cr, uid, worked_ids[0])
            res[ids[0]] = worked.number_of_days
            return res
        else:
            res[ids[0]] = 0
            return res

    def _check_date(self, cr, uid, ids, fields, arg, context=None):
        res = {}

        comp_date_from = time.strftime('%Y-04-01')
        comp_date_to = time.strftime('%Y-02-28')
        obj_payslip = self.pool.get('hr.payslip')
        payslip_ids = obj_payslip.search(
            cr, uid, [('contract_id', '=', ids[0]),
                      ('date_from',
                       '<',
                       comp_date_from),
                      ('date_to', '>', comp_date_to)]
        )
        if payslip_ids:
            res[ids[0]] = True
            return res
        else:
            res[ids[0]] = False
            return res

    def _check_voucher(self, cr, uid, ids, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)

        for contract in self.browse(cr, uid, ids):
            if user.company_id.check_benefits:
                return True
            else:
                if contract.value_va == 0 or contract.value_vr == 0:
                    return True
                else:
                    return False
        return True

    _columns = {
        'value_va': fields.float('Valley Food', help='Daily Value Benefit'),
        'value_vr': fields.float('Meal valley', help='Daily Value Benefit'),
        'workeddays': fields.function(_get_worked_days, type='float'),
        'transportation_voucher': fields.float(
            'Valley Transportation',
            help='Percentage of monthly deduction'
        ),
        'health_insurance_father': fields.float(
            'Employee Health Plan',
            help='Health Plan of the Employee'
        ),
        'health_insurance_dependent': fields.float(
            'Dependent Health Plan',
            help='Health Plan for Spouse and Dependents'
        ),
        'calc_date': fields.function(_check_date, type='boolean'),
        'aditional_benefits': fields.float(
            'Aditional Benefits',
            help='Others employee benefits'
        ),
        'ir_value': fields.function(
            _get_wage_ir, type="float",
            digits_compute=dp.get_precision('Payroll')
        ),
    }

    _constraints = [[_check_voucher,
                     u"""The company settings do not allow the use
                     of food voucher and simultaneous meal""",
                     ['value_va',
                      'value_vr']]]

    _defaults = {
        'value_va': 0,
        'value_vr': 0
    }
