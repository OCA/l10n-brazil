1. Abra **Fiscal → DeRE → Períodos de Tabela** e crie uma vigência da
   empresa (`iniValid` / `fimValid` opcional). As declarações mensais
   escolhem o período que cobre o `perApur`.
2. Gere os eventos de tabela D-1001 e depois D-1011 a partir do período
   de tabela. A declaração mensal não cria nem substitui esses eventos.
   O XML gravado permanece sem assinatura e é conferido contra o XSD
   oficial. O envio assina cada evento (XML-DSig RSA-SHA256), valida o
   evento assinado e o lote, e posta um tipo por lote. **Substituir** /
   **Excluir** na linha do evento aceito abrem o assistente (`tpOper`
   2/3) só daquele evento, para uma mudança de PGCC substituir o D-1011
   sem reenviar o D-1001. A substituição atualiza o snapshot do PGCC no
   lugar (por exemplo um `codTrib` novo) para as linhas de D-1101 /
   D-1106 manterem o vínculo da conta. Contas ainda usadas por esses
   eventos não podem ser removidas.
   Registros em rascunho ou gerados podem ser apagados no formulário.
   Enviados ou aceitos só saem se um gerente ligar **Permitir excluir
   registros DeRE aceitos** na empresa (`tpAmb` 2) ou usar Excluir
   (`tpOper` 3) na RFB.
3. O envio **não** consulta na hora. Use **Consultar Resultados** ou
   aguarde o cron (backoff exponencial de 2 até 60 minutos) até chegar
   o recibo D-9001. Depois gere o balancete (D-1101) a partir dos
   `account.move.line` lançados. O botão do balancete fica oculto até
   D-1001 e D-1011 serem aceitos.
4. Gere o D-1199 com **Encerrar Período** (`tpOper` só inclusão). Isso
   só grava o XML; a declaração permanece em *Balancete pronto*. Use
   **Descartar Encerramento Local** para dropar um D-1199 que nunca foi
   enviado. Transmita os periódicos em lote separado. Eventos de tabela
   e periódicos no mesmo lote são rejeitados. A declaração vira
   *Encerrada* quando o retorno do D-1199 é aceito.
5. Para reabrir um período oficialmente encerrado, aguarde o recibo do
   D-1199 e então **Reabrir Período**. Isso monta o D-1198
   (`nrReciboReab`) e mantém a declaração *Encerrada*; use **Descartar
   Reabertura Local** para dropar um D-1198 que nunca foi enviado.
   **Transmitir Periódicos** e consulte até o D-1198 ser aceito antes
   de substituir o balancete (`tpOper` 2 + o último recibo do D-1101).
   Uma segunda inclusão (`tpOper` 1) é rejeitada enquanto esse D-1101
   estiver ativo. Exclua (`tpOper` 3) primeiro se o mês precisar
   recomeçar. A declaração permanece *Reaberta* no retrabalho até o
   novo D-1199 ser aceito.
   **Consultar Resultados** só aparece enquanto um lote estiver
   `sent`.
   O botão azul do cabeçalho é o próximo passo oficial do mês: gerar o
   balancete, transmitir ou consultar periódicos, depois D-1106 /
   D-1121 quando a empresa for sujeita, e encerrar. Geração e envio de
   tabelas ficam no período de tabela.
   **Gerar Balancete** some depois que o D-1101 é enviado ou aceito.
   Enquanto o mês está aberto, **Substituir** / **Excluir** na linha
   do evento aceito (`tpOper` 2/3) refazem ou baixam aquele evento.
   Depois do D-1198 aceito a ação primária é substituir o balancete
   (use Substituir na linha do D-1101). **Transmitir Periódicos**
   aparece só enquanto um XML periódico estiver `generated`.

O recibo (`nrRecibo`) e o protocolo do lote ficam separados em cada
evento. Não envie uma segunda inclusão de um evento ativo. Substitua
ou exclua (`tpOper` 2/3) enquanto o mês estiver aberto; D-1198/D-1199
permanecem só inclusão. Depois do primeiro D-1199 aceito, o D-1121 só
admite retificação (`tpOper` 4) no mês reaberto. Se a empresa for
sujeita ao D-1106, gere esse evento depois do balancete (use
`semAplic` quando não houver ativos de reserva). Se for sujeita ao
D-1121, carregue os documentos de entrada dedutíveis ou marque
*Declarar inexistência de deduções*.

Toda conta analítica DeRE precisa de `codTrib` antes de gerar o
D-1011. Os códigos de tributação aparecem como `código - nome` e
aceitam busca por qualquer um dos dois. O `vApur` do D-1101 segue a
fórmula oficial de movimento (valor bruto do lado da natureza mais
ajustes). Contas de natureza variável (`natCta` V) tomam `natVApur` do
lado de fechamento do período. Estornos entram como `vAjusteDebt` /
`vAjusteCred`. O encerramento D-1199 é bloqueado quando os saldos
finais do D-1106 não batem com o D-1101, ou quando o recibo do D-1011
usado para montar o D-1101 mudou. Uma chave de documento fiscal
(`chDFe`) não pode se repetir no mesmo `perApur`. A substituição de
tabela só altera a vigência quando as datas novas diferem do período
atual. A retificação do D-1121 após a reabertura exige um `finEvt`
explícito e os documentos a retificar.

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
D-9199. **Imprimir apuração da RFB** (e o menu Imprimir) gera um PDF
paisagem dessa aba.

O D-9001 traz o extrato de vigência da tabela (D-1001 ou D-1011):
todas as vigências em vigor e cada mês sem cobertura. O extrato mais
recente de cada tabela substitui o anterior e aparece na aba
**Extrato de vigência da RFB** dos períodos de tabela. Cada vigência
é ligada ao período local pelo recibo. Quando a RFB corta um período
porque uma vigência posterior começa depois dele (`indAjusteAuto` =
1), o período ganha um **Fim da vigência efetiva** e deixa de cobrir
meses seguintes. Um aviso mostra o corte e as lacunas, e o chatter
lista recibos que não pertencem a nenhum período local.

## Checklist de homologação

Use uma empresa cujo plano já mapeie ao menos uma conta de taxa de
administração (`codTrib` 120110006) e um passivo de repasse (também
com `codTrib`). Os lançamentos do mês de apuração devem separar **taxa
própria** versus **repasse da operadora**. O balancete nunca é
digitado: ele é reconstruído a partir desses movimentos.

1. Troque para a empresa e abra **Fiscal → DeRE → Períodos de Tabela**.
2. Crie ou reutilize a vigência que cobre o mês. Confira o `iniValid`.
3. **Gerar Tabelas**. Os eventos D-1001 e D-1011 precisam existir com
   XML.
   - D-1001: `regTribPrinc` = 2 e `tpAtividade` = `02A` para
     administradora de benefícios. Sem `servFinanc` / `prognosticos`
     salvo se um regime secundário exigir.
   - D-1011: `planoCtaRef` e `freqEncerr` presentes; `cDbrMista` com
     três dígitos; toda conta analítica com `codTrib`.
4. Abra **Fiscal → DeRE → Declarações** (`perApur` = `YYYY-MM`). Depois
   que as tabelas forem aceitas, **Gerar Balancete**. Os totais do
   rodapé precisam do `brl_currency_id` oculto.
   - Linha de taxa: crédito = receita própria e `vApur` igual a esse
     crédito bruto menos ajustes a crédito mais ajustes a débito.
   - Linha de repasse: movimento presente e `vApur` segue a mesma
     regra da natureza da conta.
5. Abra cada formulário de evento e confira o XML: datas em
   `YYYY-MM-DD`; `perApur` em `YYYY-MM`. Todo `id` de evento segue
   `DeRE` + código do evento + `1` + raiz do CNPJ com zeros +
   timestamp de Brasília + sequencial `QQQQQ`. A geração já rejeita
   XML que falha o XSD oficial.
6. Se a empresa for sujeita ao D-1106, **Gerar D-1106** antes de
   encerrar. O PGCC precisa incluir ao menos uma conta com `codTrib`
   de D-1106 (MS1135). A flag da empresa sozinha não torna o D-1106
   oficial: sem esse código o evento fica oculto e não é exigido
   antes do D-1121 ou do D-1199 (MS1147). Cadastre os ativos de
   reserva técnica em **Fiscal → Configuração → DeRE → Ativos de
   Reserva Técnica**, ou o evento sai com `semAplic=1` quando essas
   contas não tiverem ativos no mês. Com exatamente um ativo por
   conta, os valores do período vêm dos lançamentos: débitos viram
   `vVarMensal`, créditos viram `vPrincLiqResg`, e o rendimento no
   mesmo lançamento (ou na conta de rendimento de reserva mapeada)
   preenche `vRendPerReceb` / `vRendLiqResg`. Vários ativos na mesma
   conta continuam manuais. Regenerar refaz esses valores 1:1.
   Se for sujeita ao D-1121, **Carregar Deduções** a partir das
   operações de entrada marcadas como dedutíveis DeRE e então **Gerar
   D-1121**. Documentos fiscais em `em_digitacao` são ignorados.
   **Substituir**, **Excluir** e **Retificar** (`tpOper` 2/3/4) ficam
   na linha do evento aceito; o D-1106 tem o mesmo par Substituir /
   Excluir.
   Quando o período não tem documento dedutível, a carga informa a
   ausência e grava `indInexistDedu`. **Encerrar Período** fica oculto
   até a carga rodar, para o mês não ser encerrado sem dedução por
   acidente.
7. **Encerrar Período** gera o D-1199 mas não trava o mês. Transmita
   os periódicos um tipo por vez: D-1101, depois D-1106 (se houver),
   depois D-1121 (se houver), depois D-1199. Cada evento auxiliar
   precisa do recibo de processamento anterior. Se o XML estiver
   errado e ainda `generated`, **Descartar Encerramento Local** e gere
   de novo.
8. Confirme que a empresa tem certificado A1. O envio assina o
   payload; o formulário do evento continua mostrando o XML sem
   assinatura.
9. Repita com **Consultar Resultados**, ou aguarde o job **DeRE:
   consultar resultados dos lotes enviados**. O POST só devolve um
   protocolo (`1.NNNNNN.N` ou `2.NNNNNN.N`); aceite e `nrRecibo` vêm
   do GET posterior. Processamento (`cdResposta` 1) deixa o lote
   enviado para o cron repetir com backoff. Erros de lote
   (`cdResposta` 4, 5, 7 ou 9) rejeitam os eventos. Um retorno D-1199
   bem-sucedido coloca a declaração em *Encerrada*.
10. **Não** envie tabelas e periódicos no mesmo lote. Não envie D-1011
    antes do D-1001 ser aceito, nem D-1199 antes do D-1101 ter recibo
    de processamento.
11. **Reabrir Período** só depois que o D-1199 for aceito com recibo
    `1199-YYYYMM-...`. Então envie o D-1198 e consulte. O próximo
    D-1101 é uma substituição (`tpOper` 2 + último recibo ativo), não
    uma segunda inclusão.

O D-3201 fica de fora deste checklist. `infoImovel` do D-1121 e
exclusões judiciais (`motExcl` 1, evento D-1021) ainda não são
gerados.
