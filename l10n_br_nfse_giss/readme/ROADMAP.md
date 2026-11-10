- Tomador no exterior, comércio exterior (grupo `comExt`) e NFS-e de fatura em
  moeda estrangeira: dependem dos dados de comércio exterior no `l10n_br_nfse`
  e do código ISO numérico do país. Hoje o envio para tomador no exterior é
  recusado com uma mensagem.
- Substituição de NFS-e (`SubstituirNfse`).
- Ler de volta os valores de IBS/CBS calculados pela prefeitura no retorno
  (`IBSCBSTotal`).
- Um RPS por lote: o webservice aceita até 50.
