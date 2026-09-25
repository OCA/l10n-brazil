- Migrar o `xml_builder` para a [derelib](https://github.com/Escodoo/derelib)
  (binding xsdata do DeRE 1.2.0, o mesmo papel da nfelib na NF-e /
  CT-e / MDF-e): montar, assinar, lotear e ler retornos pela
  biblioteca, mantendo as regras de negócio (`tpOper`, MS1135 /
  MS1147, checagens de PGCC) neste módulo. Não introduzir
  `spec_driven_model.StackedModel` antes dessa migração.
- Não herdar mixins de evento (D-1001 / D-1011 / D-1101 / D-1199) em
  `l10n_br_dere.declaration`, `l10n_br_dere.table.period` ou
  `l10n_br_dere.event`: esses abstracts compartilham `dere12_id` e
  `dere12_tpOper`.
- O `tpOper` oficial 1/2/3 (e o `4` do D-1121 depois do primeiro
  D-1199) está implementado. D-1198 / D-1199 permanecem só inclusão.
- `infoImovel` do D-1121 e D-1021 (exigido antes de `motExcl` 1)
- Réplica local da MS1155 (`perApur` futuro): a regra oficial não
  interrompe o processamento, e a suíte de testes usa meses futuros
- Eventos transacionais (D-3201 e demais D-22xx / D-32xx) depois que
  o CGIBS publicar um leiaute transacional estável
- Conteúdo do D-9199 ainda não gravado: `gCoeficientes` (serviços
  financeiros e concursos de prognósticos) e o detalhe `infoBCN` /
  `detBCN` da base negativa acumulada por origem. Só os saldos
  negativos finais ficam nas linhas de apuração.
- Os retornos D-9121 (operações com títulos públicos) e D-9209
  (transacional) são reconhecidos e validados, mas o conteúdo não é
  aplicado até os eventos correspondentes existirem.
- Lançamento contábil opcional do IBS / CBS apurado no D-9199; hoje
  os valores são gravados só para referência.
- `gUtilizBCN` do D-1199 (aproveitamento de base negativa). O grupo é
  opcional (`usarBCNAcum` / `metodoAproveit` / `detBCNeg`). A Tabela
  12 oficial (`codBC` / `codBCNRaiz`) entra com essa funcionalidade,
  não como catálogo avulso agora: o D-9199 já devolve `xDetBC` em
  cada linha de apuração.
- D-2101 (títulos públicos) fica fora do escopo de operadoras de
  planos de saúde.
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
