## 16.0.2.0.0

- O Balanço e a DRE deixam de ser quatro modelos por prefixo de conta (um par
  por plano) e passam a ser **um Balanço e uma DRE** que selecionam as contas
  pela classificação contábil, valendo para qualquer plano, inclusive
  customizado. Até a versão 14.0 esse papel era dos tipos de conta brasileiros,
  que a versão 16.0 do Odoo eliminou.
- O Balanço ganha a linha **Resultado do Exercício**. Sem ela o resultado do
  período não aparecia em lugar nenhum e o balanço fechava com o ativo maior
  que o passivo mais o patrimônio líquido, pela diferença exata do lucro.
- Correções de seleção de conta que vinham desde a migração para a 16.0: os
  Lucros Acumulados apontavam para uma conta de compensação inexistente, o
  grupo de Lucros e Prejuízos Acumulados era contado duas vezes no patrimônio
  líquido, e as linhas de IRPJ e de CSLL apontavam para prefixos que não
  existem em nenhum dos dois planos.
- O módulo passa a instalar **relatórios prontos** e os **períodos fiscais
  brasileiros** (mês de competência, trimestre de apuração e exercício social),
  em vez de entregar só os modelos.

Os modelos antigos (`balanco_patrimonial_generic`, `balanco_patrimonial_simple`,
`dre_generic` e `dre_simple`) foram removidos. Relatórios montados sobre eles
precisam ser refeitos sobre os novos.
