- As famílias de esquema do **envelope do lote assíncrono**
  (`envioLoteEventosAssincrono-v1_00_00`,
  `retornoLoteEventosAssincrono-v1_00_00`) e da **consulta de recibos**
  (`retornoRecibosChaveEvento-v1_05_01`) não têm mixins aqui. Elas têm versão
  própria (1.00.00 e 1.05.01), e gerá-las com o mesmo prefixo `reinf21_` faria
  os tipos `Reinf`, `TStatus` e `TArquivoReinf` colidirem com conteúdos
  diferentes no mesmo nome de modelo Odoo. Enquanto essas famílias não forem
  geradas com prefixo próprio, o envelope do lote e a consulta de recibos são
  montados diretamente com os bindings da `nfelib`, no `l10n_br_reinf`, sem
  persistência no ORM (o lote guarda apenas protocolo e recibo).

- O modelo raiz `reinf.21.reinf` é a união dos 23 arquivos de evento: cada um
  declara a raiz `Reinf` com o seu próprio filho (`reinf21_evtInfoContri`,
  `reinf21_evtRetPJ` e assim por diante) e o Odoo funde as declarações em um
  único modelo abstrato. Como nenhum campo aponta para essa raiz, ela nunca é
  materializada em tabela, e a serialização do envelope `<Reinf>` é feita pelo
  binding. Se um dia a raiz precisar virar modelo concreto, ela terá de ser
  gerada por evento.

- Duas linhas de `_binding_type` do R-4010 e do R-4020 (o grupo `ideAdv`, com o
  caminho `Reinf.EvtRetPx.IdeEstab.IdeBenef.IdePgto.InfoPgto.InfoProcJud.DespProcJud.IdeAdv`)
  foram quebradas à mão em concatenação implícita para caber nas 88 colunas do
  `ruff`. É a única edição manual sobre o código gerado, e ela volta a ser
  necessária a cada regeração: o correto é o `xsdata-odoo` quebrar strings
  longas, e a correção pertence ao gerador.

- Não há mixins de eventos da série R-2000 anteriores ao leiaute 2.1.2 nem
  compatibilidade com o leiaute 1.5.x: a recepção do leiaute antigo foi
  desativada junto com o web service síncrono.
