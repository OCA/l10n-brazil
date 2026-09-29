Núcleo da apuração assistida de IBS/CBS instituída pelo artigo 46 da Lei
Complementar 214/2025 e regulamentada pelo Decreto 12.955/2026 (CBS) e pela
Resolução CGIBS 6/2026 (IBS).

No novo modelo a administração tributária calcula o saldo mensal a partir dos
documentos fiscais eletrônicos do contribuinte e o apresenta para confirmação.
O contribuinte não apura mais do zero: a apuração própria existe só como
ajuste da que foi apresentada, e confirmar, ajustar ou **ficar em silêncio**
constituem o crédito tributário.

Este módulo cobre a parte independente do tributo desse ciclo:

- períodos mensais de apuração por empresa e tributo, com os prazos
  regulamentares (apresentação até o dia 15, ou até o dia 20 quando o
  contribuinte está obrigado à DeRE, e confirmação até o último dia útil do
  mês seguinte);
- o ciclo assíncrono das solicitações, inclusive a cota diária imposta pelo
  gateway;
- conciliação das linhas apresentadas com os documentos fiscais escriturados,
  classificando cada diferença e sugerindo como corrigi-la;
- inventário do escriturado, visível mesmo antes do download, com o CBS/IBS
  esperado de cada documento autorizado do período;
- avisos de prazo e expiração automática, para que o silêncio nunca passe
  despercebido.

O transporte HTTP não faz parte deste módulo. A CBS é servida pela Receita
Federal e o IBS pelo CGIBS, cada um com os seus endpoints, então a transmissão
e o parse do arquivo ficam em addons de transporte que implementam os hooks
`_transmit` e `_parse_payload`.
