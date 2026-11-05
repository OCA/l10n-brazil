- DANFSe do QWeb (l10n_br_nfse) ainda mostra os valores na moeda da
  fatura (le doc.amount_* direto).
- Emissao direta pelo ADN (l10n_br_nfse_nacional) nao converte os valores
  (nfse10_vServ e tributos leem a linha) nem preenche o grupo nfse10_comExt.
- Campos de comercio exterior da NFS-e municipal do Focus NFe nao existem
  na API documentada.
- Movimentacao temporaria de bens e MDIC do comExt ficam fixos ("nao" e
  "nao enviar").
