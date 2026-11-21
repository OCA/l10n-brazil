- O DANFSe do QWeb (l10n_br_nfse) ainda mostra os valores na moeda da
  fatura (lê doc.amount_* direto).
- A emissão direta pelo ADN (l10n_br_nfse_nacional) não converte os valores
  (nfse10_vServ e tributos leem a linha) nem preenche o grupo nfse10_comExt.
- Os campos de comércio exterior da NFS-e municipal do Focus NFe não existem
  na API documentada.
- A movimentação temporária de bens e o MDIC do comExt ficam fixos ("não" e
  "não enviar").
