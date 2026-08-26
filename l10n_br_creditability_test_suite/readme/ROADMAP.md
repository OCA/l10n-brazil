- Só cobre compra. Devolução e nota de crédito não estão cobertas, embora a
  perna de devolução da repartição de imposto seja área de risco conhecida.
- Não cobre entrada sem pedido de compra. `_apply_price_difference()` só age
  sobre linhas com `purchase_line_id`; numa entrada de NF-e avulsa o custo
  ficaria bruto em silêncio.
- As contas são procuradas por código (`1.1.9.0.01`, `1.1.3.1.02`,
  `5.1.1.1.01`, `1.1.4.1.*`), o que amarra a suíte ao `l10n_br_coa_generic`.
- O eixo `anglo_saxon_accounting` não é exercitado. Medições anteriores
  mostraram que desligá-lo deixa a conta ponte sem contrapartida e produz dupla
  contagem, em qualquer estratégia de custo — não discrimina entre elas.
