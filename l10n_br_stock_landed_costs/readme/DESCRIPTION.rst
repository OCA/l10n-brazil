Custos que chegam em documento fiscal separado da NF de compra — frete
(CT-e), despesas aduaneiras, serviços vinculados — devem compor o custo de
aquisição do estoque (Art. 301 RIR/2018, CPC 16), rateados sobre os
recebimentos correspondentes.

Este módulo permite gerar um *landed cost* (``stock.landed.cost``) a partir
de um documento fiscal de entrada, com uma linha de custo por linha do
documento pelo valor **líquido** (``stock_cost_unit`` × quantidade): o ICMS
creditável do frete, por exemplo, vira crédito fiscal e **não** é rateado no
estoque.

Para evitar dupla contagem, não gere landed cost de frete que já veio
destacado (``freight_value``) na própria NF de compra — aquele valor já
compõe o custo do recebimento.
