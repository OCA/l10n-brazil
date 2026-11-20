- Venda do bem que está com o locatário (rota *Sell Rented Product*): continua
  com a operação de venda do pedido. Falta definir o tratamento fiscal (venda
  de ativo, retorno simbólico da remessa).
- A NF-e de retorno não referencia a NF-e de remessa (refNFe).
- Faturamento periódico (mensal) de contratos longos: o `sale_rental` fatura o
  período inteiro pelo pedido.
- As rotas do `sale_rental` pertencem à empresa principal; em multiempresa é
  preciso compartilhá-las (sem empresa) para alugar em outra empresa.
