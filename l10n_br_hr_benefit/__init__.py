# -*- coding: utf-8 -*-

from . import models
from . import wizards


# DONE: Criar campos para fluxos pré-aprovados:
#   - Beneficio;
#   - Prestação de contas;
# DONE: Usabilidade, dominio dos campos Beneficios;
# Done: Display name
# Done: Inativar o registro cado a data final seja atingida.

# Done: Intervalo de datas
#       Fazer via python para ver se não coincide no memso intevalo de datas
# Done: Criar campo para anexar comprovantes
# Doing: Criar estado e fluxo de aprovação
# Doing Mileo: Criar wizard para geração apuração de compentencias.

# Done: Bloquear campos para edição, dependo do state do objeto;
# DONE: Criar campo relacioando os as pretações de conta de um benefício;
# DONE: Remover a edição e criação em alguns campos;

# TODO: Validar tipo de beneficiário;
# TODO: Criar permissões de segurança e regras de acesso;
#   A criação de beneficios deve ser feita somente pelos grupos:
#      oficial e gerente;

# TODO: Criar filtros e agrupamentos para as visões

# TODO: Verificar campos que precisam de ondelete='restrict'
# TODO: Pensar no tipo de pensão: Variável e fixo;
# TODO: Criar cron para gerar as competências automaticamente;

