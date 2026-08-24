O campo *Schema NFS-e Paulistana* na empresa escolhe entre o layout legado
(Versão 1, fato gerador até 31/12/2025) e o da Reforma Tributária (Versão 2, com
IBS/CBS). Os dois conjuntos de bindings vêm do `nfselib.paulistana` (pacotes
`v02` e `v03`, respectivamente), a partir da versão 0.3.0.

A serialização do RPS já cobre os dois layouts. Os envelopes de consulta e
cancelamento, porém, são montados pelo `erpbrasil.edoc`, e a versão publicada da
biblioteca não aceita a versão de schema como parâmetro: o `versao_schema` que
este módulo envia é descartado, com aviso no log, enquanto esse suporte não for
publicado (ver
[erpbrasil.edoc#94](https://github.com/erpbrasil/erpbrasil.edoc/pull/94)). Até
então, consulta e cancelamento usam o envelope legado mesmo com o schema da
Reforma selecionado.

Pontos que ainda precisam de confirmação no Manual de Orientação (MOC) da NFS-e
de São Paulo, hoje preenchidos com defaults conservadores:

- `ExigibilidadeSuspensa` e `PagamentoParceladoAntecipado` (fixos em 0);
- `indDest` (fixo em 0, destinatário é o próprio tomador);
- largura da `InscricaoPrestador` dentro do grupo `ChaveRPS` no layout da
  Reforma (mantida em 8 posições, como no legado; a assinatura do RPS usa 12).
