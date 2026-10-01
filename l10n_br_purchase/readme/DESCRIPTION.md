Este módulo integra a parte fiscal do módulo `l10n_br_fiscal` com o
módulo de compra purchase do Odoo. O módulo permite o cálculo dos
impostos brasileiros já no pedido de compra e propaga a operação fiscal
até a nota fiscal de compra, deixando ela com a tributação mais correta
possível para seu financeiro (sendo que vocẽ poderia também importar o
XML da nota depois).

O relatório de compra também é estendido para apresentar os impostos
brasileiros.

Este módulo é indicado para a compra de itens com NFe's. Mas se você
quer gerenciar suas notas de entradas de acordo com o recebimento do
material, você pode também ter interesse no módulo
`l10n_br_purchase_stock` que permite isso.

Para notas de entrada importadas (NFe), o módulo oferece ainda:

- **Atualizar o pedido de compra a partir da NFe**: recalcula a
  quantidade, o preço e os impostos das linhas do pedido de compra de
  acordo com a nota fiscal importada, a partir da referência do pedido
  informada no XML (`xPed`/`nItemPed`).
- **Criar um pedido de compra a partir da NFe**: gera um novo pedido de
  compra rascunho com o mesmo parceiro, operação fiscal, linhas,
  quantidades, preços e tributos da nota fiscal importada.
