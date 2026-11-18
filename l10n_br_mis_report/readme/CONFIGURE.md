Os relatórios selecionam as contas pela **classificação contábil brasileira**
(as etiquetas de conta do `l10n_br_coa`), não pelo código da conta. Quem usa os
planos `l10n_br_coa_generic` ou `l10n_br_coa_simple` não precisa configurar
nada: eles já vêm classificados.

Num **plano de contas próprio**, classifique as contas para que elas apareçam:
vá em **Faturamento > Configuração > Plano de Contas**, abra a conta e preencha
**Etiquetas** com a linha de relatório correspondente (por exemplo "Ativo /
Circulante / Estoques" ou "Resultado / (-) Despesas Administrativas").

Toda conta de resultado leva **duas** etiquetas: a da sua linha na DRE e a
etiqueta guarda-chuva "Resultado / Contas de Resultado (todas)". É essa segunda
que alimenta a linha "Resultado do Exercício" do Balanço, que é o que faz o
ativo fechar com o passivo mais o patrimônio líquido.

Conta sem etiqueta simplesmente não entra nos relatórios legais, que é o
comportamento desejado para contas de controle interno.
