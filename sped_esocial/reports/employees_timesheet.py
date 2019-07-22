# -*- coding: utf-8 -*-
# (c) 2019 Kmee - Hugo Borges <hugo.borges@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import datetime

from openerp import api
from openerp.addons.report_py3o.py3o_parser import py3o_report_extender


class Contrato(object):
    def __init__(self):
        self.idx = ''
        self.matricula_contrato = ''
        self.nome_empregado = ''
        self.cargo = ''
        self.lotacao = ''
        self.ctps_numero = ''
        self.ctps_serie = ''
        self.entrada = ''
        self.intervalo = ''
        self.saida = ''

class Empresa(object):
    def _init_(self):
        self.nome = ''
        self.rua = ''
        self.rua2 = ''
        self.zip = ''
        self.cidade = ''
        self.uf = ''
        self.cnpj = ''
        self.logo = ''
        self.footer = ''

@api.model
@py3o_report_extender(
    'sped_esocial.employees_timesheet_py3o_report')
def employees_timesheet(pool, cr, uid, localcontext, context):
    self = localcontext['objects']

    company_id = self.company_id
    contratos = []
    notes = ""
    sorted_contracts = \
        sorted(self.contract_ids, key=lambda c: c.employee_id.name)
    for idx, contract_id in enumerate(sorted_contracts, start=1):
        contrato = Contrato()
        contrato.idx = idx

        attendance_id = contract_id.working_hours.attendance_ids[:1]
        turno_id = attendance_id.turno_id
        horario_intervalo = turno_id.horario_intervalo_ids[:1]

        contrato.matricula_contrato = contract_id.matricula_contrato or ''

        contrato.nome_empregado = contract_id.employee_id.name or ''
        contrato.cargo = contract_id.job_id.name or ''
        contrato.lotacao = company_id.cod_lotacao or ''

        contrato.entrada = turno_id.hr_entr + 'h' if turno_id else ''
        contrato.intervalo = \
            ('%sh às %sh' %
             (horario_intervalo.ini_interv,
              horario_intervalo.term_interv)) if horario_intervalo else '',
        contrato.saida = turno_id.hr_saida + 'h' if turno_id else ''

        contrato.ctps_numero = contract_id.employee_id.ctps or ''
        contrato.ctps_serie = contract_id.employee_id.ctps_series or ''

        contratos.append(contrato)
        notes += "#{}- {} .".format(idx, contract_id.notes) \
            if contract_id.notes else ''

    empresa = Empresa()
    empresa.nome = company_id.partner_id.name or ''
    empresa.rua = company_id.street or ''
    empresa.rua2 = company_id.street2 or ''
    empresa.zip = company_id.zip or ''
    empresa.cidade = company_id.l10n_br_city_id.name or ''
    empresa.uf = company_id.state_id.code or ''
    empresa.cnpj = company_id.partner_id.cnpj_cpf or ''
    empresa.footer = company_id.rml_footer or ''

    company_logo = company_id.logo
    company_nfe_logo = company_id.nfe_logo

    data = {
        "data_hoje": datetime.now().strftime('%d/%m/%Y'),
        "empresa": empresa,
        "contratos": contratos,
        "notes": notes,
        "company_logo": company_nfe_logo if company_nfe_logo else company_logo,
        "company_logo2": company_nfe_logo if company_nfe_logo else company_logo
    }

    localcontext.update(data)
