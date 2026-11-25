## Fluxo mensal

1. Em **Fiscal → DeRE → Períodos de Tabela**, crie ou reutilize a
   vigência da empresa (`iniValid` / `fimValid` opcional). Cada
   declaração mensal usa o período que cobre o seu `perApur`.
2. No período de tabela, **Gerar Tabelas** cria o D-1001 e o D-1011. A
   declaração mensal não cria nem substitui eventos de tabela.
3. **Transmitir Tabelas** e **Consultar Resultados** até os dois
   eventos serem aceitos. O D-1011 só é enviado depois que o D-1001 for
   aceito.
4. Em **Fiscal → DeRE → Declarações**, crie o mês (`perApur` =
   `AAAA-MM`) e use **Gerar Balancete**. O D-1101 é montado a partir
   dos lançamentos contábeis postados; o balancete nunca é digitado. O
   botão fica oculto até D-1001 e D-1011 serem aceitos e some depois
   que o D-1101 é enviado ou aceito.
5. Se a empresa for sujeita ao D-1106, use **Gerar D-1106**. Sem ativos
   de reserva no mês, o evento sai com `semAplic=1`.
6. Se a empresa for sujeita ao D-1121, use **Carregar Deduções** e
   depois **Gerar D-1121**. Sem documento dedutível no período, a carga
   avisa e liga **Declarar inexistência de deduções**. **Encerrar
   Período** fica oculto até a carga rodar, para o mês não ser
   encerrado sem dedução por acidente.
7. **Encerrar Período** gera o D-1199 (só inclusão). Isso só grava o
   XML: a declaração continua em *Balancete pronto*. **Descartar
   Encerramento Local** apaga um D-1199 que nunca foi enviado.
8. **Transmitir Periódicos** envia o próximo evento gerado, um tipo por
   lote, na ordem D-1101, D-1106, D-1121 e D-1199. Consulte entre um
   envio e outro: cada evento exige o recibo de processamento do
   anterior. A declaração vira *Encerrada* quando o D-1199 é aceito.

O botão azul do cabeçalho da declaração é sempre o próximo passo oficial
do mês. **Transmitir Periódicos** só aparece enquanto houver um XML
periódico gerado, e **Consultar Resultados** só enquanto houver um lote
enviado.

O XML gravado fica sem assinatura e é conferido contra o XSD oficial na
geração. O envio assina cada evento (XML-DSig RSA-SHA256), valida o
evento assinado e o lote e posta um tipo de evento por lote; tabelas e
periódicos no mesmo lote são rejeitados. O envio não consulta na hora:
o POST só devolve o protocolo, e o aceite e o `nrRecibo` vêm da
consulta seguinte, manual ou pelo cron (backoff exponencial de 2 a 60
minutos). O recibo e o protocolo do lote ficam separados em cada
evento.

O `vApur` do D-1101 segue a fórmula oficial de movimento: valor bruto
do lado da natureza mais ajustes. Contas de natureza variável (`natCta`
V) tomam `natVApur` do lado de fechamento do período, e estornos entram
como `vAjusteDebt` / `vAjusteCred`. O encerramento é bloqueado quando os
saldos finais do D-1106 não batem com o D-1101, ou quando o recibo do
D-1011 usado no D-1101 mudou.

## Substituir, excluir e reabrir

Não envie uma segunda inclusão de um evento ativo. **Substituir** e
**Excluir** na linha de um evento aceito abrem o assistente (`tpOper`
2 / 3) só daquele evento:

- No período de tabela, uma mudança de PGCC substitui o D-1011 sem
  reenviar o D-1001. A substituição atualiza o snapshot do PGCC no lugar
  (por exemplo um `codTrib` novo) e as linhas do D-1101 / D-1106
  mantêm o vínculo da conta. Contas ainda usadas por esses eventos não
  podem ser removidas. A substituição só altera a vigência quando as
  datas novas diferem das do período atual.
- Na declaração, enquanto o mês está aberto, **Substituir** /
  **Excluir** refazem ou baixam o D-1101, o D-1106 ou o D-1121. Exclua
  (`tpOper` 3) o D-1101 se o mês precisar recomeçar do zero.
- D-1198 e D-1199 são só inclusão.

Para reabrir um período oficialmente encerrado:

1. Aguarde o recibo do D-1199 (`1199-AAAAMM-...`) e use **Reabrir
   Período**. Isso monta o D-1198 (`nrReciboReab`) e mantém a
   declaração *Encerrada*. **Descartar Reabertura Local** apaga um
   D-1198 que nunca foi enviado.
2. **Transmitir Periódicos** e consulte até o D-1198 ser aceito. A
   declaração passa a *Reaberta*.
3. Substitua o balancete na linha do D-1101 (`tpOper` 2 com o último
   recibo ativo). Uma nova inclusão é rejeitada enquanto esse D-1101
   estiver ativo.
4. Depois do primeiro D-1199 aceito, o D-1121 só admite retificação
   (**Retificar**, `tpOper` 4), com um `finEvt` explícito e os
   documentos a retificar.
5. Gere e envie um novo D-1199. A declaração volta a *Encerrada* quando
   ele é aceito.

Registros em rascunho ou gerados podem ser apagados no formulário.
Enviados ou aceitos só saem com **Excluir** (`tpOper` 3) na RFB, ou se
um gerente ligar **Permitir excluir registros DeRE aceitos** na empresa
em ambiente de testes (`tpAmb` 2).

## Exportações (XLSX e PDF)

**Baixar XLSX**, no cabeçalho da declaração, do período de tabela ou do
evento, exporta as grades oficiais com os mesmos campos do XML: D-1011,
D-1101, D-1106, D-1121 (documentos e itens) e os totais D-9101, quando
existirem. Eventos só de cabeçalho (D-1001, D-1198, D-1199) não têm
planilha.

**Imprimir Apuração da RFB** (ou o menu Imprimir da declaração) gera um
PDF paisagem da aba **Apuração da RFB**.

## Eventos de retorno (D-9xxx)

Cada evento consultado guarda o próprio retorno. A aba **Retorno** do
evento mostra o tipo (D-9001, D-9101, D-9106, D-9112, D-9198 ou
D-9199), a sequência de versão (`seqEvento`), os horários de recepção
e processamento, o recibo do D-1011 usado pela RFB (`nrReciboPGCC`) e
o XML de retorno. O retorno é conferido contra o XSD oficial:
diferenças vão para o chatter do evento e nunca desfazem a decisão da
RFB.

A aba **Apuração da RFB** da declaração lista os totais D-9101 por
`codTrib` / `indTribISS` e o total D-9106 ao lado do `vApur` enviado
no D-1101 / D-1106. Um aviso e uma nota no chatter aparecem quando um
total difere ou quando D-9101, D-9106 ou D-9112 usaram outro recibo de
PGCC que o D-1011 em vigor.

Quando o D-1199 é aceito, a mesma aba mostra a apuração D-9199: as
bases IBS/CBS por regime específico (`detBC`), os totais gerais
(`totalTributosGeral`) e os recibos de D-1101, D-1106 e D-1121 usados
no encerramento. O aviso também aparece quando esses recibos não são
os eventos em vigor. Os valores são gravados só para referência; não
se cria lançamento contábil. Depois que o D-1198 reabre o período, a
apuração anterior permanece visível e é substituída pelo próximo
D-9199.

O D-9001 traz o extrato de vigência da tabela (D-1001 ou D-1011):
todas as vigências em vigor e cada mês sem cobertura. O extrato mais
recente de cada tabela substitui o anterior e aparece na aba
**Extrato de vigência da RFB** dos períodos de tabela. Cada vigência
é ligada ao período local pelo recibo. Quando a RFB corta um período
porque uma vigência posterior começa depois dele (`indAjusteAuto` =
1), o período ganha um **Fim de vigência efetiva** e deixa de cobrir
meses seguintes. Um aviso mostra o corte e as lacunas, e o chatter
lista recibos que não pertencem a nenhum período local.

## Checklist de homologação

Use uma empresa em ambiente de testes (`tpAmb` 2) cujo plano já mapeie
as contas movimentadas no mês, todas com `codTrib`, e poste os
lançamentos do mês antes de gerar o balancete.

1. Período de tabela: o `iniValid` cobre o mês, e D-1001 e D-1011
   existem com XML.
   - D-1001: `regTribPrinc`, `tpAtividade` e os grupos opcionais
     (`servFinanc`, `prognosticos`) batem com a aba DeRE da empresa.
   - D-1011: `planoCtaRef` e `freqEncerr` presentes, `cDbrMista` com
     três dígitos e toda conta analítica com `codTrib`.
2. Balancete: confira saldo inicial, débitos, créditos, saldo final e
   `vApur` de algumas contas contra o razão. O rodapé da grade soma só
   débitos e créditos; saldos e `vApur` dependem da natureza de cada
   conta e não são totalizados.
3. XML dos eventos: datas em `AAAA-MM-DD` e `perApur` em `AAAA-MM`. Todo
   `id` de evento segue `DeRE` + código do evento + `1` + raiz do CNPJ
   com zeros + timestamp de Brasília + sequencial `QQQQQ`.
4. D-1106, se a empresa for sujeita: o PGCC inclui ao menos uma conta
   com `codTrib` de D-1106 (MS1135). Sem esse código o evento fica
   oculto e não é exigido antes do D-1121 ou do D-1199 (MS1147). Com
   exatamente um ativo por conta, débitos viram `vVarMensal`, créditos
   viram `vPrincLiqResg` e o rendimento (no mesmo lançamento ou na
   conta de rendimento mapeada) preenche `vRendPerReceb` /
   `vRendLiqResg`. Vários ativos na mesma conta continuam manuais.
5. D-1121, se a empresa for sujeita: a carga traz só documentos fiscais
   de entrada, de operações marcadas como **Dedutível na DeRE**, com
   chave de acesso e data dentro do mês. Os tipos suportados são NF-e
   (55), NFC-e (65) e NFS-e (SE). Documentos em digitação, rejeitados,
   cancelados, denegados ou inutilizados ficam de fora. Uma chave
   (`chDFe`) não pode se repetir no mesmo `perApur`.
6. Ordem de envio: tabelas e periódicos nunca no mesmo lote; D-1011 só
   depois do D-1001 aceito; D-1106, D-1121 e D-1199 só depois do recibo
   de processamento dos eventos anteriores.
7. Consulta: o POST devolve só o protocolo (`1.NNNNNN.N` ou
   `2.NNNNNN.N`). `cdResposta` 1 (em processamento) deixa o lote
   enviado para o cron repetir; `cdResposta` 4, 5, 7 ou 9 rejeitam os
   eventos do lote.
8. Reabertura: **Reabrir Período** só depois do D-1199 aceito com
   recibo. O D-1101 seguinte é substituição (`tpOper` 2), não uma
   segunda inclusão.

O D-3201 fica de fora deste checklist. `infoImovel` do D-1121 e
exclusões judiciais (`motExcl` 1, evento D-1021) ainda não são
gerados.
