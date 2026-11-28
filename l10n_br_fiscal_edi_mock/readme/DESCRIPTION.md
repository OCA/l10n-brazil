Simula a SEFAZ na emissao de documentos fiscais, no mesmo espirito do
`l10n_br_fiscal_dfe_mock` (que simula a distribuicao de DF-e).

Com o modo ligado na empresa, e so em homologacao:

- NF-e e NFC-e: a camada de transmissao da `erpbrasil.edoc` e trocada por uma
  que devolve os retornos da SEFAZ (status do servico, consulta, autorizacao do
  lote, eventos de cancelamento e carta de correcao). Assinatura, montagem do
  `nfeProc` e mudanca de estado rodam pelo codigo real.
- CT-e e MDF-e: o documento a enviar recebe um protocolo simulado e passa a
  autorizado.

Todo retorno traz "(SEFAZ SIMULADA)" no motivo, `verAplic` `SEFAZ-SIMULADA` e
protocolo iniciado por 9. O formulario do documento mostra um aviso.
