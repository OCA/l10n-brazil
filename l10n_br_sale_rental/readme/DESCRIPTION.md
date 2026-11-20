Integra a locação de bens móveis do `sale_rental` (OCA/vertical-rental) com a
localização brasileira.

Na locação o bem sai e volta para a locadora sem mudar de dono, e o aluguel é
cobrado à parte:

- **Remessa** (retirada): NF-e sem destaque de ICMS/IPI/PIS/COFINS e sem título
  a receber, CFOP 5908/6908, pelo valor do bem.
- **Retorno** (devolução): locatário não contribuinte de ICMS (construtora,
  pessoa física), a locadora emite NF-e de entrada CFOP 1909/2909; locatário
  contribuinte emite a própria NF-e de retorno (5909/6909) e a transferência
  não fica para faturar.
- **Aluguel**: operação "Locação de bens móveis", sem ISS (STF Súmula
  Vinculante 31) e sem ICMS, PIS/COFINS pelo regime da empresa, documento
  NFS-e (obrigatória para locação de bens móveis desde 01/12/2026, Ato Conjunto
  RFB/CGIBS 4/2026).

O `sale_rental` já gera as transferências por regras de estoque (Rental In para
Rental Out na retirada e o caminho inverso na devolução). Este módulo dá a elas
tipos de operação próprios ("Rental Delivery" e "Rental Return") com as
operações fiscais de comodato/locação do `l10n_br_fiscal`, faturáveis pelo
faturamento de transferências (`stock_picking_invoicing`). A linha de serviço
do aluguel recebe a operação de locação, e o `l10n_br_sale` separa a fatura do
aluguel (NFS-e) da venda de mercadorias (NF-e) quando o pedido tem as duas.
