Apuração de imposto sobre consumo por período: ICMS, IPI, PIS e COFINS.

Uma apuração é um lote por período, por grupo de imposto e por regime.
Ela lê os saldos das move lines (via `account_tax_balance`), aceita os
ajustes que não saem da contabilidade, confronta débitos com créditos,
transporta o saldo credor de um período para o seguinte e gera o
lançamento de encerramento usando as contas que o `account.tax.group` do
core já modela.

A memória de cálculo fica persistida. É ela que as escriturações fiscais
serializam: o bloco E da EFD ICMS/IPI e o bloco M da EFD Contribuições
são saídas de uma apuração, não cálculos próprios. Sem esta camada, cada
escrituração recalcula do zero e os números não fecham entre si nem com
a contabilidade.

Os totais são publicados na mesma estrutura do registro E110, campo a
campo, de modo que a escrituração apenas leia.
