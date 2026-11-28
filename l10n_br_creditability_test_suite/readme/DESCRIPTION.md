Régua neutra para medir como o custo de aquisição do estoque se comporta ao
longo do ciclo completo de compra: pedido, recebimento, fatura e **confirmação
da fatura**.

O último passo é a razão de existir do módulo. É na confirmação que o
`purchase_stock` chama `_apply_price_difference()`, compara a camada de
valoração contra o preço da linha da fatura e, havendo diferença, grava uma
camada de correção. Enquanto essa comparação usar o preço bruto, ela devolve ao
estoque exatamente o imposto recuperável que um custo líquido tenha tirado —
silenciosamente, numa camada filha que ninguém abre.

## Neutralidade

A suíte não referencia nenhum campo introduzido por um PR específico. Ela afirma
só sobre o que existe no core e na localização: camadas de valoração
(`stock.valuation.layer`), linhas de lançamento (`account.move.line`) e saldos
de conta contábil.

É isso que permite rodar o mesmo arquivo em checkouts diferentes e atribuir a
diferença nos números à diferença entre as estratégias de custo, não entre os
testes. O relatório **exibe** campos como `cost_unit` quando existem, como
diagnóstico, mas nenhum assert depende deles.

## Os invariantes

| | invariante | o que pega |
|---|---|---|
| **I1** | delta da conta ponte no ciclo é zero | crédito pendurado na conta ponte |
| **I2** | camada de valoração e conta de estoque iguais ao líquido que a fatura debitou na conta da linha | o custo voltar ao bruto depois de confirmar a fatura |
| **I3** | delta das contas `a Compensar` igual aos impostos creditados pela fatura | crédito virar espelho em conta de resultado em vez de ativo |
| **I4** | delta do CMV é zero num ciclo sem venda | dupla contagem |
| **I5** | com pedido e fatura de valores diferentes, a correção é a diferença **líquida**, nunca o valor do imposto | o ajuste de preço lançar imposto em vez de diferença |
| **I6** | os saldos com `deductible_taxes` ligado são iguais aos com ele desligado | a flag mudar resultado em vez de só apresentação |

O oráculo de I2 é calculado em `_bill_net_on_line_account`, somando as linhas de
produto com as linhas de imposto que foram para a mesma conta. É escrito de
forma independente do código de produção de propósito, para o teste não virar
tautologia.
