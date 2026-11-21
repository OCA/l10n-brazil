Valoriza a entrada de estoque já pelo custo líquido de aquisição, isto é, sem
os tributos recuperáveis. Sem este módulo o recebimento nasce pelo valor cheio
e o custo só fica correto quando a fatura do fornecedor é confirmada.

O módulo é **opcional**: o `l10n_br_stock_account` já garante o custo líquido
no fechamento da fatura, comparando a camada de valoração com o valor que a
fatura efetivamente debita na conta da linha. O que este módulo muda é *quando*
o custo fica certo - na entrada, em vez de na fatura -, evitando que o estoque
fique valorizado pelo bruto no intervalo entre o recebimento e o faturamento.

É o mesmo desenho que o Protheus faz pela TES (`Cred. ICMS`) e o SAP pelo
*tax code* do pedido: quem decide se o imposto entra no custo é a operação,
e o recebimento já nasce certo.
