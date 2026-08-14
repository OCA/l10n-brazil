O módulo já instala os relatórios prontos. Acesse **Faturamento > Relatórios >
Relatórios SIG** e escolha um deles:

- **Balanço Patrimonial - exercício atual e anterior**: a apresentação
  comparativa que a Lei 6.404/76 manda publicar (art. 176, § 1º), com a coluna
  de variação.
- **DRE - exercício atual e anterior**: a mesma comparação, para o resultado.
- **DRE - mês e acumulado no exercício**: o acompanhamento gerencial corrente,
  com o mês, o acumulado desde 1º de janeiro e as duas colunas equivalentes do
  exercício anterior.
- **DRE - trimestral**: o trimestre em que se apura o IRPJ e a CSLL no lucro
  presumido e no lucro real trimestral (Lei 9.430/96, art. 1º), com o trimestre
  anterior e o mesmo trimestre do exercício passado.

Para ver outro período, mude a **data base** do relatório: todas as colunas se
reposicionam juntas, porque são declaradas relativas a ela, não por data fixa.

Depois clique em **Visualizar**, **Imprimir** ou **Exportar**. No modo de
visualização, clicar no valor de uma linha detalhada abre os lançamentos que a
compõem.

## Períodos

O módulo instala três tipos de período (**Faturamento > Configuração >
Intervalos de Datas**), que se geram sozinhos daí em diante:

- **Mês de competência**, que é o período da apuração de ICMS, IPI, PIS e
  COFINS e da escrituração mensal do SPED;
- **Trimestre de apuração**, o trimestre civil do IRPJ e da CSLL;
- **Exercício social**, de um ano (Lei 6.404/76, art. 175).

## Montar um relatório próprio

Duplique um dos prontos e ajuste as colunas, ou crie um novo escolhendo o
modelo BP ou DRE. Em **Colunas**, cada coluna pode ser uma data fixa ou um
período relativo à data base: "Tipo de período" Ano com "Deslocamento" 0 é o
exercício corrente, -1 o anterior. Marque **Acumulado no ano** para a coluna
começar em 1º de janeiro.

Uma ressalva do Balanço: a coluna precisa cobrir o exercício (o exercício
inteiro ou um acumulado desde 1º de janeiro), porque o resultado do período é
lido do movimento das contas de resultado. Numa coluna de mês isolado, o
patrimônio líquido exibiria só o resultado daquele mês.
