Liga a GNRE à contabilidade: a postagem da fatura de venda cria a obrigação de
recolhimento, e a emissão da guia cria a conta a pagar contra a Secretaria da
Fazenda da UF favorecida.

O parceiro credor vem da regra por UF. Sem ele na regra, é resolvido pela UF de
destino com o `_get_tax_authority_partner` do `l10n_br_account_withholding`,
quando esse módulo estiver instalado, e por fim cai no parceiro do grupo fiscal.
