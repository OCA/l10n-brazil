**EFD-Reinf** (Escrituração Fiscal Digital de Retenções e Outras Informações
Fiscais) para o Odoo. Desde a extinção da DIRF, para fatos geradores a partir
de 01/01/2025, as retenções de IR, CSLL, PIS e COFINS sobre pagamentos a
terceiros são declaradas nos eventos da série R-4000, que alimentam a DCTFWeb
pelos totalizadores. É obrigação mensal corrente: quando os pagamentos a
fornecedores nascem no Odoo, não há como declarar o Reinf em outro sistema.

Este módulo é a **fundação** dessa escrituração. Ele traz o motor de eventos, os
cadastros de apoio e o ambiente de transmissão. A geração dos eventos, a
apuração por competência, a tela de conferência e o transporte REST vêm nas
fases seguintes, listadas no `ROADMAP`.

## O que já está aqui

- **R-1000** (`l10n_br_reinf.r1000`): o evento de cadastro do contribuinte,
  montado a partir da configuração da empresa e **serializado em XML conferido
  contra o XSD oficial** antes de ser gravado como anexo do evento. O R-1000 é
  declaração versionada (tem período de validade e é alterado por
  `novaValidade`), por isso é modelo próprio, um registro por evento, e não
  campos em `res.company`: a empresa guarda a configuração, e cada evento copia
  o que valia no momento em que foi montado, para o XML de um evento passado
  continuar reproduzível.
- **Apuração da competência** (`l10n_br_reinf.calculation`): a declaração nasce
  do pagamento e do crédito, e o fato gerador é por tributo, então a mesma nota
  alimenta duas competências (IR pelo crédito, PCC pelo pagamento). A tela da
  apuração é a tela de conferência: linhas com divergência, exceções
  enumeradas com o registro de origem e o que fazer, DARFs espelho e eventos
  gerados.
- **Naturezas de rendimento e códigos de receita, das tabelas oficiais**: 297
  naturezas e 1576 linhas de mapeamento (evento, tributo, código de receita,
  periodicidade, residência fiscal no exterior, classificação tributária 85),
  **cada linha com a sua vigência**, porque as tabelas trocam o código de receita
  sem a natureza mudar. A fonte é o pacote "EFD-REINF Tabelas" do portal SPED,
  em XLSX, e não o PDF do manual; o conversor está em
  `scripts/generate_annex_data.py`. As marcações de retenção da natureza são
  lidas desse mapeamento, então a marcação e o código de receita não contam
  histórias diferentes.

- **Motor de eventos** (`l10n_br_reinf.event`): um registro por evento, com o
  identificador de 36 posições do leiaute (`ID` + tipo e número de inscrição do
  contribuinte + momento da geração + sequencial), o XML de envio e o de
  retorno em `ir.attachment`, o ciclo de vida do rascunho ao recibo, a cadeia
  de retificação por `nrRecibo` e a origem polimórfica (um evento do Reinf não
  nasce de documento fiscal: nasce de pagamento, de fechamento ou do próprio
  cadastro da empresa). Os nomes de campo espelham o `l10n_br_fiscal.event` do
  `l10n_br_fiscal_edi`, para quem já lê um evento fiscal ler este também.
- **Lote** (`l10n_br_reinf.batch`): o agrupamento que vai ao serviço de
  recepção assíncrona, com as regras que não são questão de gosto: no máximo 50
  eventos (o que o envelope do leiaute aceita), grupo homogêneo, e evento de
  fechamento nunca no mesmo lote dos periódicos, porque a Receita processa os
  eventos de um lote em paralelo, sem ordem garantida.
- **Ocorrências** (`l10n_br_reinf.occurrence`): os erros e avisos devolvidos
  pela Receita, guardados como registro, para a conferência listar o motivo da
  rejeição em vez de pedir que alguém leia um XML.
- **Cadastros**: natureza de rendimento (`natRend`, com as marcações de quais
  retenções ela admite) e código de receita do DARF (com a periodicidade que
  define em qual totalizador do R-9015 o código aparece). Os dois herdam o
  `l10n_br_fiscal.data.abstract`, então já vêm com vigência (`date_start` /
  `date_end`), busca por código e o mesmo comportamento das outras tabelas
  fiscais da localização. Alíquota e código são dado com vigência, nunca
  constante no código.
- **Ambiente** (`res.company.reinf_environment`): produção ou produção
  restrita, **sem default**. Escolher entre os dois é decisão do contribuinte,
  e um chute manda dado real para o ambiente errado; por isso o campo é exigido
  na transmissão, e não preenchido em silêncio.

## O que ainda não está

Não há transporte: `_transport_send()` e `_transport_query()` são a interface
única de saída do Odoo e levantam `NotImplementedError`. Isso é deliberado: o
resto do módulo é escrito e testado contra um mock antes de existir cliente
REST, e o CI da OCA nunca chama a Receita.
