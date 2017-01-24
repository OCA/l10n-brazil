# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models
from datetime import datetime

TIPO_DE_FOLHA = [
    ('normal', u'Folha normal'),
    ('rescisao', u'Rescisão'),
    ('ferias', u'Férias'),
    ('decimo_terceiro', u'Décimo terceiro (13º)'),
    ('licenca_maternidade', u'Licença maternidade'),
    ('auxilio_doenca', u'Auxílio doença'),
    ('auxílio_acidente_trabalho', u'Auxílio acidente de trabalho'),
]


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    tipo_de_folha = fields.Selection(
        selection=TIPO_DE_FOLHA,
        string=u'Tipo de folha',
        required=True,
        default='normal',
    )

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
            dias_mes = self.env['resource.calendar'].get_dias_base(
                fields.Datetime.from_string(date_from),
                fields.Datetime.from_string(date_to)
            )
            result += [self.get_attendances(u'Dias Base', 1, u'DIAS_BASE',
                                            dias_mes, 0.0, contract_id)]

            # get dias uteis
            dias_uteis = self.env['resource.calendar'].quantidade_dias_uteis(
                fields.Datetime.from_string(date_from),
                fields.Datetime.from_string(date_to),
            )
            result += [self.get_attendances(u'Dias Úteis', 2, u'DIAS_UTEIS',
                                            dias_uteis, 0.0, contract_id)]
            # get faltas
            leaves = {}
            hr_contract = self.env['hr.contract'].browse(contract_id.id)
            leaves = self.env['resource.calendar'].get_ocurrences(
                hr_contract.employee_id.id, date_from, date_to)
            if leaves.get('faltas_nao_remuneradas'):
                qtd_leaves = leaves['quantidade_dias_faltas_nao_remuneradas']
                result += [self.get_attendances(u'Faltas Não remuneradas', 3,
                                                u'FALTAS_NAO_REMUNERADAS',
                                                qtd_leaves,
                                                0.0, contract_id)]
            # get Quantidade de DSR
            quantity_DSR = hr_contract.working_hours. \
                quantidade_de_DSR(date_from, date_to)
            if quantity_DSR:
                result += [self.get_attendances(u'DSR do Mês', 4,
                                                u'DSR_TOTAL', quantity_DSR,
                                                0.0, contract_id)]
            # get discount DSR
            quantity_DSR_discount = self.env['resource.calendar']. \
                get_quantity_discount_DSR(leaves['faltas_nao_remuneradas'],
                                          hr_contract.working_hours.leave_ids,
                                          date_from, date_to)
            if leaves.get('faltas_nao_remuneradas'):
                result += [self.get_attendances(u'DSR a serem descontados', 5,
                                                u'DSR_PARA_DESCONTAR',
                                                quantity_DSR_discount,
                                                0.0, contract_id)]

            quantidade_dias_ferias = self.env['resource.calendar'].\
                get_quantidade_dias_ferias(hr_contract.employee_id.id,
                                           date_from, date_to)
            if quantidade_dias_ferias:
                result += [self.get_attendances(u'Quantidade dias em Férias',
                                                6, u'FERIAS',
                                                quantidade_dias_ferias, 0.0,
                                                contract_id)]
            return result

    def INSS(self, BASE_INSS):
        tabela_inss_obj = self.env['l10n_br.hr.social.security.tax']
        inss = tabela_inss_obj._compute_inss(BASE_INSS, self.date_from)
        return inss

    def IRRF(self, BASE_IR, BASE_INSS):
        tabela_irrf_obj = self.env['l10n_br.hr.income.tax']
        inss = self.INSS(BASE_INSS)
        irrf = tabela_irrf_obj._compute_irrf(
            BASE_IR, self.employee_id.id, inss, self.date_from
        )
        return irrf

    @api.model
    def get_contract_specific_rubrics(self, contract_id, rule_ids):
        contract = self.env['hr.contract'].browse(contract_id)
        for rule in contract.specific_rule_ids:
            if datetime.strftime(
                    datetime.now(), '%Y-%m-%d') >= rule.date_start:
                if not rule.date_stop or datetime.strftime(
                        datetime.now(), '%Y-%m-%d') <= rule.date_stop:
                    rule_ids.append((rule.rule_id.id, rule.rule_id.sequence))
        return rule_ids

    def get_specific_rubric_value(self, rubrica_id):
        for rubrica in self.contract_id.specific_rule_ids:
            if rubrica.rule_id.id == rubrica_id:
                return rubrica.specific_quantity * \
                       (rubrica.specific_percentual/100) * \
                       rubrica.specific_amount

    def get_payslip_lines(self, cr, uid, contract_ids, payslip_id, context):
        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict, category.parent_id, amount)
            localdict['categories'].dict[category.code] = category.code in localdict['categories'].dict and localdict['categories'].dict[category.code] + amount or amount
            return localdict

        class BrowsableObject(object):
            def __init__(self, pool, cr, uid, employee_id, dict):
                self.pool = pool
                self.cr = cr
                self.uid = uid
                self.employee_id = employee_id
                self.dict = dict

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        class InputLine(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                result = 0.0
                self.cr.execute("SELECT sum(amount) as sum\
                            FROM hr_payslip as hp, hr_payslip_input as pi \
                            WHERE hp.employee_id = %s AND hp.state = 'done' \
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s",
                           (self.employee_id, from_date, to_date, code))
                res = self.cr.fetchone()[0]
                return res or 0.0

        class WorkedDays(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def _sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                result = 0.0
                self.cr.execute("SELECT sum(number_of_days) as number_of_days, sum(number_of_hours) as number_of_hours\
                            FROM hr_payslip as hp, hr_payslip_worked_days as pi \
                            WHERE hp.employee_id = %s AND hp.state = 'done'\
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s",
                           (self.employee_id, from_date, to_date, code))
                return self.cr.fetchone()

            def sum(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[0] or 0.0

            def sum_hours(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[1] or 0.0

        class Payslips(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                self.cr.execute("SELECT sum(case when hp.credit_note = False then (pl.total) else (-pl.total) end)\
                            FROM hr_payslip as hp, hr_payslip_line as pl \
                            WHERE hp.employee_id = %s AND hp.state = 'done' \
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id AND pl.code = %s",
                            (self.employee_id, from_date, to_date, code))
                res = self.cr.fetchone()
                return res and res[0] or 0.0

        #we keep a dict with the result because a value can be overwritten by another rule with the same code
        result_dict = {}
        rules = {}
        categories_dict = {}
        blacklist = []
        payslip_obj = self.pool.get('hr.payslip')
        inputs_obj = self.pool.get('hr.payslip.worked_days')
        obj_rule = self.pool.get('hr.salary.rule')
        payslip = payslip_obj.browse(cr, uid, payslip_id, context=context)
        worked_days = {}
        for worked_days_line in payslip.worked_days_line_ids:
            worked_days[worked_days_line.code] = worked_days_line
        inputs = {}
        for input_line in payslip.input_line_ids:
            inputs[input_line.code] = input_line

        categories_obj = BrowsableObject(self.pool, cr, uid, payslip.employee_id.id, categories_dict)
        input_obj = InputLine(self.pool, cr, uid, payslip.employee_id.id, inputs)
        worked_days_obj = WorkedDays(self.pool, cr, uid, payslip.employee_id.id, worked_days)
        payslip_obj = Payslips(self.pool, cr, uid, payslip.employee_id.id, payslip)
        rules_obj = BrowsableObject(self.pool, cr, uid, payslip.employee_id.id, rules)

        baselocaldict = {
            'CALCULAR':payslip, 'BASE_INSS': 0.0, 'BASE_FGTS': 0.0,
            'BASE_IR': 0.0, 'categories': categories_obj, 'rules': rules_obj,
            'payslip': payslip_obj, 'worked_days': worked_days_obj,
            'inputs': input_obj, 'rubrica': None
        }
        #get the ids of the structures on the contracts and their parent id as well
        structure_ids = self.pool.get('hr.contract').get_all_structures(cr, uid, contract_ids, context=context)
        #get the rules of the structure and thier children
        rule_ids = self.pool.get('hr.payroll.structure').get_all_rules(cr, uid, structure_ids, context=context)
        rule_ids = self.get_contract_specific_rubrics(
           cr, uid, contract_ids, rule_ids, context=context
        )
        #run the rules by sequence
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]

        for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
            employee = contract.employee_id
            localdict = dict(baselocaldict, employee=employee, contract=contract)
            for rule in obj_rule.browse(cr, uid, sorted_rule_ids, context=context):
                key = rule.code + '-' + str(contract.id)
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                localdict['result_rate'] = 100
                localdict['rubrica'] = rule
                #check if the rule can be applied
                if obj_rule.satisfy_condition(cr, uid, rule.id, localdict, context=context) and rule.id not in blacklist:
                    #compute the amount of the rule
                    amount, qty, rate = obj_rule.compute_rule(cr, uid, rule.id, localdict, context=context)
                    #check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                    #set/overwrite the amount computed for this rule in the localdict
                    tot_rule = amount * qty * rate / 100.0
                    localdict[rule.code] = tot_rule
                    rules[rule.code] = rule
                    if rule.compoe_base_INSS:
                        localdict['BASE_INSS'] += tot_rule
                    if rule.compoe_base_IR:
                        localdict['BASE_IR'] += tot_rule
                    if rule.compoe_base_FGTS:
                        localdict['BASE_FGTS'] += tot_rule
                    #sum the amount for its salary category
                    localdict = _sum_salary_rule_category(localdict, rule.category_id, tot_rule - previous_amount)
                    #create/overwrite the rule in the temporary results
                    result_dict[key] = {
                        'salary_rule_id': rule.id,
                        'contract_id': contract.id,
                        'name': rule.name,
                        'code': rule.code,
                        'category_id': rule.category_id.id,
                        'sequence': rule.sequence,
                        'appears_on_payslip': rule.appears_on_payslip,
                        'condition_select': rule.condition_select,
                        'condition_python': rule.condition_python,
                        'condition_range': rule.condition_range,
                        'condition_range_min': rule.condition_range_min,
                        'condition_range_max': rule.condition_range_max,
                        'amount_select': rule.amount_select,
                        'amount_fix': rule.amount_fix,
                        'amount_python_compute': rule.amount_python_compute,
                        'amount_percentage': rule.amount_percentage,
                        'amount_percentage_base': rule.amount_percentage_base,
                        'register_id': rule.register_id.id,
                        'amount': amount,
                        'employee_id': contract.employee_id.id,
                        'quantity': qty,
                        'rate': rate,
                    }
                else:
                    #blacklist this rule and its children
                    blacklist += [id for id, seq in self.pool.get('hr.salary.rule')._recursive_search_of_rules(cr, uid, [rule], context=context)]

        result = [value for code, value in result_dict.items()]
        return result
