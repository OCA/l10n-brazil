Apuração de imposto sobre consumo por período: ICMS, IPI, PIS e COFINS.

Uma apuração é um lote por período e por grupo de imposto; o regime de
apuração (cumulativo ou não cumulativo) mora no grupo, e contribuinte com
receita mista configura um grupo por regime. Assim uma apuração nunca mistura
regimes nem conta a mesma linha duas vezes.
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

Escopo de estabelecimento: a apuração pertence a uma company, e cada
company representa um estabelecimento (um CNPJ). Para ICMS e IPI isso
espelha a legislação, que apura por estabelecimento. Para PIS e COFINS,
que a pessoa jurídica apura de forma centralizada, esta versão atende a
PJ cujo movimento está numa única company; consolidar apurações de
múltiplos estabelecimentos numa apuração central da matriz está fora do
escopo desta versão (ver o roadmap).
