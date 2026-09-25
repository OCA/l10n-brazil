Após importar e validar uma NFe como fatura de fornecedor
(`l10n_br_nfe`/`l10n_br_fiscal`), o cabeçalho da fatura apresenta duas
ações para integrar o pedido de compra:

- **Update PO from NFe**: abre um assistente que sugere o pedido de
  compra do fornecedor por meio da referência `xPed`/`nItemPed`
  informada no XML. Cada linha do pedido pode ter a quantidade e o preço
  unitário atualizados (convertidos para a unidade do pedido), com a
  opção de recalcular os impostos a partir da nota importada.
- **Create PO from NFe**: cria um novo pedido de compra em estado
  rascunho a partir da fatura importada, preenchendo parceiro, operação
  fiscal, referência do documento (`partner_ref`), linhas, quantidades,
  preços e tributos fiscais do documento.