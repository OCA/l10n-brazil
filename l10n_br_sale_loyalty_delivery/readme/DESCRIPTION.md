Este módulo integra o *l10n_br_delivery* com o *sale_loyalty_delivery*.

O *l10n_br_delivery* não cria a linha de entrega no pedido de venda: o
valor do frete fica em `amount_freight_value` e é rateado nas linhas de
produto, como exige a NF-e. A recompensa "Frete grátis" do Odoo calcula o
desconto a partir da linha de entrega e, sem ela, entra no pedido valendo
zero.

Com este módulo, a recompensa de frete grátis passa a usar o valor do
frete do pedido, respeitando o desconto máximo configurado na recompensa.
