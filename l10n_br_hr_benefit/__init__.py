# -*- coding: utf-8 -*-

from . import models
from . import wizards


# DONE: Criar campos para fluxos pré-aprovados:
#   - Benefício;
#   - Prestação de contas;
# DONE: Usabilidade, dominio dos campos Benefícios;
# Done: Display name
# Done: Inativar o registro cado a data final seja atingida.

# Done: Intervalo de datas
#       Fazer via python para ver se não coincide no memso intevalo de datas
# Done: Criar campo para anexar comprovantes
# Done: Criar estado e fluxo de aprovação
# Done: Criar wizard para geração apuração de compentencias.

# Done: Bloquear campos para edição, dependo do state do objeto;
# DONE: Criar campo relacioando os as pretações de conta de um benefício;
# DONE: Remover a edição e criação em alguns campos;

# DONE: Validar tipo de beneficiário;
# DONE: Remover botão de adicionar benefícios;

# DONE: Verificar campos que precisam de ondelete='restrict'
             # Tipo do benefício
             # Beneficiário
# DONE: Criar filtros e agrupamentos para as visões
             # Benefícios
                # Agrupar por Tipo de benefício
                # Agrupar por Contrato
             # Prestação de Contas
# DONE: Regras de segurança

# DONE: Criar magic buttons no cadastro de beneficiários;
        # Mostrar benefícios do beneficiário

# DONE: Corrigir magic buttons no cadastro de Beneficios;
        # Filtrar apenas Apurações do benefício selecionado

# DONE: Criar permissões de segurança e regras de acesso;
#   A criação de Benefícios deve ser feita somente pelos grupos:
#      oficial e gerente;

# TODO: Pensar no tipo de pensão: Variável e fixo;
    # Deixar para depois

# TODO: Campos para histórico e data
#      dos valores; como em odoo/parts/addons/hr/hr_employee_benefit
    # Prioridade mínima
    # parts/addons/hr/hr_employee_benefit/models/hr_employee_benefit_rate_line.py

# DONE: Criar cron para gerar as competências automaticamente;
# DOING: Integração com a folha de pagamento

# TODO: Criar dados (data) relacionados aos Benefícios
    # depois, se necessário

# DONE: validar ir action mixins
    # RH deve saber quantas apurações estão pendentes de análise

# DONE: Limite de aprovação em dias line_days_approval_limit
    # Após o limite de dias, caso não aprovado pelo funcionário,
    # somente um funcionário de RH poderá aprovar

# DONE: Validar tipo de funcionário (gerente, funcionario, cedente, etc)
    # Possibilidade de campos
        # Categoria do Contrato
        # Tipo de vínculo trabalhista
        # Regime de trabalho

# DONE: Verificar se o filho é menor que 6 meses
                    #  Benefício mensal de reembolso de 50% do valor gasto,
                    #  limitado ao teto, salvo exceções (idade até 6 meses)
                    # models/hr_contract_benefit_line.py:73

# DONE: Remover caso a folha seja cancelada ou
                #  outro estágio pertinente.
                # models/hr_payslip.py:50

# DONE: Agrupar ou não benefícios na visão do holerite
    # Criar um novo modelo hr.contract.benefit.line.payslip
        # Este modelo será responsável por agrupar hr.contract.benefit.line
        # Ele será exibido na aba "Benefícios" do holerite
            # Ou então criar uma nova Aba
        # Criar um Checkbox no tipo de benefício para controle dessa opção
