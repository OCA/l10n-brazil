O XML é montado por `models/xml_builder.py` a partir de dicionários
preparados pelos modelos e conferido contra o XSD oficial pelo
`l10n_br_dere_spec`. As linhas de grade (PGCC, balancete, reserva,
deduções e retornos) herdam os mixins planos do spec
(`dere.12.infoconta`, `dere.12.balanceteconta`, …), então os campos
`dere12_*` têm o mesmo nome das tags do XSD.

Decisões de design:

- `l10n_br_dere.declaration`, `l10n_br_dere.table.period` e
  `l10n_br_dere.event` **não** herdam os mixins de evento do spec
  (D-1001, D-1011, D-1101, D-1199, …). Esses abstracts compartilham
  `dere12_id` e `dere12_tpOper`, e um registro que agrupa vários
  eventos teria um único valor para campos que variam por evento. O
  cabeçalho de cada evento é montado em `_header_vals()`.
- O período de tabela e a declaração compartilham o envio, a consulta e
  a aplicação dos retornos em `l10n_br_dere.event.parent.mixin`
  (`models/dere_event_ops.py`). Cada modelo informa só o que difere
  pelos ganchos `_dere_batch_vals()`, `_dere_consultable_batches()`,
  `_dere_header_validity_vals()` e `_dere_after_return()`.
- Os eventos de tabela (D-1001 / D-1011) e o snapshot do PGCC pertencem
  ao período de tabela. A declaração chega a eles por
  `_require_table_period()`, que cria o período que cobre o mês quando
  ainda não existe.
- Retornos do gateway são lidos com `safe_fromstring()` do
  `l10n_br_dere_spec`, sem expandir entidades nem acessar a rede. Como
  as entidades não são resolvidas, a árvore pode ter nós de entidade e
  comentários: percorra só elementos (`iter(tag=etree.Element)`).
- `spec_driven_model.StackedModel` não é usado. Ele só passa a fazer
  sentido depois da migração do `xml_builder` para a derelib (veja o
  ROADMAP), no mesmo papel da nfelib na NF-e / CT-e / MDF-e: a
  biblioteca monta, assina, loteia e lê retornos, e este módulo mantém
  as regras de negócio (`tpOper`, MS1135 / MS1147, checagens de PGCC).
