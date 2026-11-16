- Os lançamentos contábeis da fatura (`l10n_br_account`) recalculam os impostos
  em `account.tax.compute_all` sem os valores manuais. É preciso um módulo de
  ligação para que a contabilidade use os mesmos valores do documento fiscal.
- O valor 0 significa "cálculo automático", então não é possível zerar um
  imposto manualmente. Uma evolução possível é um booleano por imposto.
- CBS e IBS já têm override manual de base/valor, igual aos demais impostos.
