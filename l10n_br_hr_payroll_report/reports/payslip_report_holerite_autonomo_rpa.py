# -*- encoding: utf-8 -*-
# Copyright (C) 2018 - ABGF
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.addons.report_py3o.py3o_parser import py3o_report_extender
from pybrasil.data import formata_data
from pybrasil.valor import formata_valor
from pybrasil.inscricao import formata_cpf

@py3o_report_extender(
    "l10n_br_hr_payroll_report.report_payslip_autonomo_py3o_report")
def payslip_autonomo_report(pool, cr, uid, local_context, context):
    payslip_autonomo_pool = pool['hr.payslip.autonomo']
    payslip_id = payslip_autonomo_pool.browse(cr, uid, context['active_id'])

    company_logo = payslip_id.company_id.logo
    company_nfe_logo = payslip_id.company_id.nfe_logo

    local_context['company_logo'] = \
        company_nfe_logo if company_nfe_logo else company_logo
    local_context['company_logo2'] = \
        company_nfe_logo if company_nfe_logo else company_logo

    # CPF DO Autonomo
    if payslip_id.employee_id.cpf:
        local_context['cpf'] = formata_cpf(payslip_id.employee_id.cpf)
    else:
        local_context['cpf'] = ''

    # Formatar Data da emissao do do RG
    local_context['rg_emission'] = \
        formata_data(payslip_id.employee_id.rg_emission)

    # Campo de conta bancária no formato para exibição do relatório
    conta_bancaria = ''
    if payslip_id.employee_id.address_home_id.bank_ids:
        conta_bancaria_id = payslip_id.employee_id.address_home_id.bank_ids[0]

        conta_bancaria = conta_bancaria_id.bank.bic + ' / ' + \
                         conta_bancaria_id.bra_number + ' / ' + \
                         conta_bancaria_id.acc_number

    local_context['conta_bancaria'] = conta_bancaria

    # Data de pagamento
    if payslip_id.data_pagamento_autonomo:
        local_context['data_pagamento'] = \
            formata_data(payslip_id.data_pagamento_autonomo)
    else:
        local_context['data_pagamento'] = ''

    # Competencia
    competencia = dict(payslip_id._fields.get('mes_do_ano').selection).get(
        payslip_id.mes_do_ano) + ' de ' + str(payslip_id.ano)
    local_context['competencia'] = competencia

    local_context['footer'] = \
        u'Telefone: 61-3246-6200 | E-mail: gepes@abgf.gov.br | ' \
        u'Site: http://www.abgf.gov.br'

    # Numero maximo de linhas por holerites, se ultrapassar esse limite será
    # dividido em 2 grupos para ser exibido em uma segunda pagina
    max_linhas = 10
    local_context['grupo_rubricas_1'] = payslip_id.line_resume_ids[:max_linhas]
    local_context['grupo_rubricas_2'] = False
    if len(payslip_id.line_resume_ids) > max_linhas:
        local_context['grupo_rubricas_2'] = \
            payslip_id.line_resume_ids[max_linhas:]
