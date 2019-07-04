# -*- coding: utf-8 -*-
# Copyright 2019 ABGF - Luciano Veras
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.report_py3o.py3o_parser import py3o_report_extender
from openerp import api

MARITAL = {'single': 'Solteiro(a)',
           'married': 'Casado(a)',
           'widower': 'Viuvo(a)',
           'divorced': 'Divorciado(a)',
           'common_law_marriage': 'Common Law Marriage',
           'separated': 'Separado(a)'}


class WorkingHoursObj(object):
    def __init__(self, working_hours):
        self.dias = working_hours[0] or '-'
        self.entrada = working_hours[1] or '-'
        self.inicio_int = working_hours[2] or '-'
        self.fim_int = working_hours[3] or '-'
        self.saida = working_hours[4] or '-'


@api.model
@py3o_report_extender('l10n_br_hr_payroll_report.report_payslip_py3o_ficha_registro')
def payslip_ficha_registro(pool, cr, uid, local_context, context):
    working_hours_dict = eval(
        pool['wizard.l10n_br_hr_employee.ficha_registro'].browse(
            cr, uid, context['active_id']).working_hours_dict)
    work_hours = []
    for val in working_hours_dict:
        work_hours.append(WorkingHoursObj(val))

    d = {'work_hours': work_hours}
    objects = local_context['objects']

    objects.ctps = objects.ctps or '-'
    objects.forma_pg = objects.forma_pg or '-'
    objects.cbo = objects.cbo or '-'
    objects.estado_civil = MARITAL[objects.marital] or '-'
    objects.father_name = objects.father_name or '-'
    objects.conjuge = objects.conjuge or '-'
    objects.mother_name = objects.mother_name or '-'
    objects.titulo_eleitoral = objects.titulo_eleitoral or '-'
    objects.wage = objects.wage or '-'
    objects.educational_attainment = objects.educational_attainment or '-'
    objects.naturalizado = objects.naturalizado or '-'
    objects.blood_type = objects.blood_type or '-'
    objects.creservist = objects.creservist or '-'
    objects.pis_pasep = objects.pis_pasep or '-'
    objects.dt_opc_fgts = objects.dt_opc_fgts or '-'
    objects.nacionalidade = objects.nacionalidade or '-'
    objects.conjuge_brasileiro = objects.conjuge_brasileiro or '-'
    objects.naturalidade = objects.naturalidade or '-'

    local_context.update(d)
