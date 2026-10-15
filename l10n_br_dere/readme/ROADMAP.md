- Migrar o `xml_builder` para a [derelib](https://github.com/Escodoo/derelib)
  (binding xsdata do DeRE 1.2.0): montar, assinar, lotear e ler
  retornos pela biblioteca, mantendo as regras de negócio neste módulo.
- `infoImovel` do D-1121 e D-1021 (exigido antes de `motExcl` 1)
- No leiaute 1.3.0 o `tpAtiv` muda de número: `06` deixa de ser plano
  de saúde. Uma base que já gravou o D-1121 com o código do 1.2.0
  precisa migrar a operação fiscal e a linha de dedução antes de
  emitir o XML do leiaute novo.
- D-9109 (`evtRetornoPMensal`), retorno dos periódicos mensais que não
  têm evento de retorno próprio, entra com o leiaute 1.3.0. Até lá um
  namespace desconhecido deixa o tipo de retorno vazio, não passa pelo
  XSD e grava o `cdRetorno` normalmente.
- Réplica local da MS1155 (`perApur` futuro): a regra oficial não
  interrompe o processamento, e a suíte de testes usa meses futuros
- Eventos transacionais (D-3201 e demais D-22xx / D-32xx) depois que
  o CGIBS publicar um leiaute transacional estável
- D-2101 (débito em operações com títulos de dívida com oferta
  pública). Quem é obrigado a ele não encerra o mês só com este
  módulo: o D-1199 é rejeitado pela regra
  `EVENTOS_OBRIGATORIOS_PERIODO` (MOD 1.3.0, 3.1.2).
- Consolidação das filiais no balancete da raiz. Cada filial tem o
  próprio plano, então a soma não é `child_of` da empresa. O D-1101
  da raiz soma pelo `cCta` da matriz: conta de filial sem esse
  mapeamento impede o encerramento, lançamento entre empresas da
  mesma raiz é eliminado e o `idAtivo` do D-1106 passa a ser único
  na raiz. O primeiro mês consolidado não herda o saldo de um D-1101
  que foi só da matriz. Até lá, a declaração e o período de tabela
  só são aceitos na empresa raiz; a matriz que já tem filial continua
  declarando o próprio razão.
- Conteúdo do D-9199 ainda não gravado: `gCoeficientes` (serviços
  financeiros e concursos de prognósticos) e o detalhe `infoBCN` /
  `detBCN` da base negativa acumulada por origem. Só os saldos
  negativos finais ficam nas linhas de apuração.
- Os retornos D-9121 (débito em operações com títulos de dívida com
  oferta pública) e D-9209
  (transacional) são reconhecidos e validados, mas o conteúdo não é
  aplicado até os eventos correspondentes existirem.
- Lançamento contábil opcional do IBS / CBS apurado no D-9199; hoje
  os valores são gravados só para referência.
- `gUtilizBCN` do D-1199 (aproveitamento de base negativa). O grupo é
  opcional (`usarBCNAcum` / `metodoAproveit` / `detBCNeg`). A Tabela
  12 oficial (`codBC` / `codBCNRaiz`) entra com essa funcionalidade,
  não como catálogo avulso agora: o D-9199 já devolve `xDetBC` em
  cada linha de apuração.
- O backoff da consulta não tem número máximo de tentativas (manual
  Dev §3.3). O atraso é limitado a 60 minutos e o lote permanece
  `sent` até chegar um resultado.
- Tabelas oficiais do Anexo I que ficam de fora deste módulo de
  propósito:
  - 13 / 15 reutilizam `res.country.state` / `res.country`
  - 14 / 22 / 23 / 24 / 32 são planos referenciais externos (SPED,
    COSIF, SUSEP, PREVIC, ANS). Pertencem a um módulo de plano de
    contas, não aqui. A MS1077 (conta ausente do plano oficial)
    permanece no servidor.
  - 33 (coeficientes etários de contraprestação) entra com o D-3201
- A MS1114 (`cCtaRef` de conta desmembrada deve coincidir com o pai)
  é só aviso na RFB e não é replicada localmente.
