# -*- coding: utf-8 -*-
# Copyright 2019 ABGF - Luciano Veras
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.report_py3o.py3o_parser import py3o_report_extender
from openerp import api
from pybrasil.data import formata_data
from pybrasil import valor


class AlteracaoCargo(object):
    def __init__(self, date_start, cargo):
        self.date_start = date_start or '-'
        self.cargo = cargo or '-'


class AlteracaoSalario(object):
    def __init__(self, date_start, wage):
        self.date_start = date_start or '-'
        self.wage = wage or '-'


class Ferias(object):
    def __init__(self, inicio_aquisitivo, fim_aquisitivo, inicio_gozo,
                 fim_gozo):
        self.inicio_aquisitivo = inicio_aquisitivo or '-'
        self.fim_aquisitivo = fim_aquisitivo or '-'
        self.inicio_gozo = inicio_gozo or '-'
        self.fim_gozo = fim_gozo or '-'


class WorkingHoursObj(object):
    def __init__(self, working_hours):
        self.dias = working_hours[0] or '-'
        self.entrada = working_hours[1] or '-'
        self.inicio_int = working_hours[2] or '-'
        self.fim_int = working_hours[3] or '-'
        self.saida = working_hours[4] or '-'


def formata_nome(string):
    return ' '.join(['{}{}'.format(x[0].upper(), x[1:].lower())
                     for x in string.split()])


@api.model
@py3o_report_extender('l10n_br_hr_payroll_report.report_payslip_py3o_ficha_registro')
def payslip_ficha_registro(pool, cr, uid, local_context, context):
    working_hours_dict = eval(
        pool['wizard.l10n_br_hr_employee.ficha_registro'].browse(
            cr, uid, context['active_id']).working_hours_dict)
    work_hours = []
    for val in working_hours_dict:
        work_hours.append(WorkingHoursObj(val))

    objects = local_context['objects']

    objects.name = formata_nome(objects.name) or '-'
    objects.matricula = objects.matricula or '-'
    objects.ctps = objects.ctps or '-'
    objects.forma_pg = objects.forma_pg or '-'
    objects.cbo = objects.cbo or '-'
    objects.estado_civil = objects.estado_civil or '-'\
        if objects.estado_civil else '-'
    objects.father_name = formata_nome(objects.father_name) or '-'
    objects.conjuge = objects.conjuge or '-'
    objects.mother_name = formata_nome(objects.mother_name) or '-'
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
    objects.dt_desligamento = objects.dt_desligamento or '-'

    alt_sal_list = []
    for salary in objects.change_salary_ids:
        date_start = formata_data(salary.date_start) or '-'
        wage = valor.formata_valor(salary.wage) or '-'
        alt_sal_list.append(AlteracaoSalario(date_start=date_start, wage=wage))

    alt_cargo_list = []
    for cargo in objects.change_job_ids:
        date_start = formata_data(cargo.date_start) or '-'
        cargo = cargo.job_id.name or ''
        alt_cargo_list.append(AlteracaoCargo(date_start=date_start,
                                             cargo=cargo))

    ferias_list = []
    for ferias in objects.vacation_control_ids:
        inicio_aquisitivo = \
            formata_data(ferias.inicio_aquisitivo) or '-'
        fim_aquisitivo = formata_data(ferias.fim_aquisitivo) or '-'
        inicio_gozo = formata_data(ferias.inicio_gozo) or '-'
        fim_gozo = formata_data(ferias.fim_gozo) or '-'
        ferias_list.append(Ferias(inicio_aquisitivo=inicio_aquisitivo,
                                  fim_aquisitivo=fim_aquisitivo,
                                  inicio_gozo=inicio_gozo,
                                  fim_gozo=fim_gozo))

    d = {'work_hours': work_hours, 'foto': objects.image_medium,
         'alt_sal': alt_sal_list, 'alt_cargo': alt_cargo_list,
         'ferias': ferias_list}

    local_context.update(d)
