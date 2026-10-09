Mensalidade da locação de bens móveis pelo contrato recorrente.

Junta o `l10n_br_sale_rental` (remessa e retorno em NF-e, aluguel com a operação
"Locação de bens móveis") com o `sale_rental_contract` (o contrato fatura o
aluguel todo mês) e o `l10n_br_product_contract` (contrato gerado pelo pedido):

- os valores fiscais da linha do contrato são recalculados para a quantidade de
  equipamentos e o preço mensal (no pedido, a linha do aluguel é em dias x diária);
- o contrato feito só de linhas de locação recebe a operação de locação, e a
  fatura mensal sai em NFS-e, sem ISS, com IBS/CBS.
