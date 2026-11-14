Emissão de NFS-e pelo webservice do GissOnline (Eicon), versão 2, usado por
municípios como Guarulhos, Santo André, Santos, Jundiaí, São José do Rio Preto,
Maceió e Campos dos Goytacazes.

O GissOnline V2 recebe RPS no leiaute ABRASF 2.04 ampliado com os grupos da
reforma tributária: tributos federais (PIS, COFINS e o tipo de retenção), carga
tributária aproximada, IBS/CBS (CST, cClassTrib e indicador de operação) e NBS.

O módulo:

- monta o lote de RPS a partir dos dados que o `l10n_br_nfse` já prepara;
- envia o lote (assíncrono, o único modo que o fornecedor recomenda), guarda o
  protocolo e consulta o lote até a nota sair;
- antes de enviar, consulta o RPS na prefeitura: depois de uma queda de conexão
  o lote pode ter sido recebido, e reenviar é recusado;
- tomador no exterior com o endereço do exterior, o NIF e o país pelo código
  ISO numérico; na exportação de serviço (exigibilidade do ISS 4, exportação, na
  linha), o serviço vai para o país do tomador com o grupo de comércio
  exterior, e a nota de fatura em moeda estrangeira sai em reais pela taxa da
  fatura, com a moeda e o valor original no grupo;
- grava o número, o código de verificação e a chave nacional da NFS-e;
- cancela a NFS-e com o motivo escolhido no documento.

A assinatura (cada RPS e depois o lote), o envelope SOAP e a transmissão com
certificado ficam no provedor `Giss` do `erpbrasil.edoc`; os tipos do leiaute,
na biblioteca `nfselib.giss`.
