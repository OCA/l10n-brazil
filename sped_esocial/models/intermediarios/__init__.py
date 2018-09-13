# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# Registros de Cadastro
from . import s1000_informacoes_do_empregador_contribuinte_orgao_publico
from . import s1005_estabelecimentos_obras_unidades_orgaos_publicos
from . import s1010_rubrica
from . import s1020_lotacao_tributaria
from . import s1030_cargos_empregos_publicos
from . import s1050_turnos_trabalho

# Registros Periódicos
from . import s1200_remuneracao_de_trabalhador_rgps
from . import s1202_remuneracao_de_servidor_rpps
from . import s1210_pagamento
from . import s1295_solicitacao_totalizador_pagamento_contingencia
from . import s1298_reaberturaPeriodo
from . import s1299_fechamento

# Registros Não Periódicos
from . import s2200_cadastramento_inicial_vinculo_admissao_trabalhador
from . import s2205_alteracao_dados_cadastrais_trabalhador
from . import s2206_alteracao_contrato_trabalho
from . import s2230_afastamento_temporario
from . import s2299_desligamento
from . import s2300_inicio_trabalhador_sem_vinculo_de_emprego
from . import s2306_alteracao_contrato_sem_vinculo
from . import s2399_desligamento_trabalhador_sem_vinculo

# Exclusão de Registros
from . import s3000_exclusao_evento

# Registros Totalizadores
from . import s5001_contribuicao_social_trabalhador
from . import s5001_infocpcalc
from . import s5001_ideestablot
from . import s5002_imposto_renda_retido_fonte
from . import s5002_basesirrf
from . import s5002_infoirrf
from . import s5011_inss_consolidado
from . import s5011_inss_consolidado_idestab
from . import s5011_inss_consolidado_idestab_basesremun
from . import s5012_irrf_consolidado
from . import s5012_irrf_consolidado_infocrcontrib
