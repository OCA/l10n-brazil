# -*- coding: utf-8 -*-
# ###########################################################################
#
#    Author: Wagner Pereira
#    Copyright 2018 ABGF - www.abgf.gov.br
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
##############################################################################


{
    'name': 'Sped e-Social',
    'version': '8.0.0.0.1',
    'category': 'Base',
    'license': 'AGPL-3',
    'author': 'ABGF',
    'website': 'http://www.abgf.gov.br',
    'depends': [
        'sped_transmissao',
        'l10n_br_hr_payroll',
        'l10n_br_hr',
        'hr_contract',
        'resource',
        'report_py3o',
    ],
    'data': [

        # Menus
        'views/sped_esocial_menu.xml',
        'views/hr_menu.xml',

        # Views
        'wizards/s2299_desligamento_wizard_view.xml',
        'wizards/hr_employee_timesheet_wizard_views.xml',
        'wizards/s3000_exclusao_wizard_view.xml',
        'views/sped_esocial_view.xml',
        'views/inherited_res_company.xml',
        'views/inherited_hr_salary_rule.xml',
        'views/inherited_hr_job.xml',
        'views/inherited_hr_contract.xml',
        'views/inherited_hr_contract_change.xml',
        'views/hr_turnos_trabalho_view.xml',
        'views/inherited_resource_calendar_attendance.xml',
        'views/inherited_resource_calendar.xml',
        'views/inherited_hr_employee.xml',
        'views/inherited_res_partner.xml',
        'views/inherited_hr_payslip_view.xml',
        'views/inherited_hr_payslip_autonomo_view.xml',
        'views/inherited_hr_holidays_status_view.xml',
        'views/inherited_hr_holidays_view.xml',
        'views/inherited_sped_registro.xml',
        'views/hr_ambiente_trabalho.xml',
        'views/hr_condicao_ambiente_trabalho.xml',
        'views/hr_informativo_atividade_trabalho.xml',
        'views/hr_fator_risco.xml',
        'views/hr_equipamento_protecao.xml',
        'views/hr_responsavel_ambiental.xml',
        'views/hr_saude_trabalhador.xml',
        'views/hr_exame_aso.xml',
        'views/hr_acidente_trabalho.xml',
        'views/hr_acidente_parte_atingida.xml',
        'views/hr_agente_causador.xml',
        'views/hr_atestado_medico.xml',
        'views/hr_treinamentos_capacitacoes.xml',
        'views/hr_professor_treinamento.xml',

        # Intermediarios
        'views/intermediarios/s1000_informacoes_do_empregador_contribuinte_orgao_publico.xml',
        'views/intermediarios/s1005_estabelecimentos_obras_unidades_orgaos_publicos.xml',
        'views/intermediarios/s1010_rubrica_view.xml',
        'views/intermediarios/s1020_lotacao_tributaria_view.xml',
        'views/intermediarios/s1030_cargos_empregos_publicos_view.xml',
        'views/intermediarios/s1050_turnos_trabalho_view.xml',
        'views/intermediarios/s1060_ambiente_trabalho.xml',
        'views/intermediarios/s1200_remuneracao_de_trabalhador_rgps.xml',
        'views/intermediarios/s1202_remuneracao_de_servidor_rpps.xml',
        'views/intermediarios/s1210_pagamento.xml',
        'views/intermediarios/s1295_solicitacao_totalizador_pagamento_contingencia_view.xml',
        'views/intermediarios/s1298_reabertura.xml',
        'views/intermediarios/s1299_fechamento.xml',
        'views/intermediarios/s2200_cadastramento_inicial_vinculo_admissao_trabalhador_view.xml',
        'views/intermediarios/s2205_alteracao_dados_cadastrais_trabalhador_view.xml',
        'views/intermediarios/s2206_alteracao_contrato_trabalho_view.xml',
        'views/intermediarios/s2210_comunicacao_acidente_trabalho.xml',
        'views/intermediarios/s2220_saude_trabalhador.xml',
        'views/intermediarios/s2230_afastamento_temporario_view.xml',
        'views/intermediarios/s2240_condicao_ambiente_trabalho.xml',
        'views/intermediarios/s2245_treinamento_capacitacao.xml',
        'views/intermediarios/s2299_desligamento_view.xml',
        'views/intermediarios/s2300_cadastramento_inicial_trabalhador_sem_vinculo.xml',
        'views/intermediarios/s2306_alteracao_contrato_trabalhador_sem_vinculo.xml',
        'views/intermediarios/s2399_termino_trabalhador_sem_vinculo.xml',
        'views/intermediarios/s3000_exclusao_evento.xml',
        'views/intermediarios/s5001_contribuicao_social_trabalhador.xml',
        'views/intermediarios/s5002_imposto_renda_retido_fonte.xml',
        'views/intermediarios/s5011_inss_consolidado.xml',
        'views/intermediarios/s5012_irrf_consolidado.xml',

        # Segurança
        'security/ir.model.access.csv',

        # Relatórios
        'reports/totalizador_periodo.xml',
        'reports/report_employees_timesheet_py3o.xml',

    ],
    "installable": True,
    "auto_install": False,
}
