**Já implementado**

- Mapeamento da DPS sobre o documento fiscal, com prestador, tomador, serviço e
  valores, e o regime tributário (MEI, Simples Nacional ou normal) deduzido da
  empresa.
- Cliente REST/mTLS com verificação de certificado do servidor, nova tentativa
  apenas em GET e sem registrar payload nem chaves em log.
- Emissão, rejeição legível, cancelamento pelo evento `101101` e consulta de
  cancelamento feito fora do Odoo.
- DANFSe gerado do XML autorizado.
- Grupo `IBSCBS` da DPS (leiaute 1.01, reforma tributária) montado a partir do
  `cClassTrib`, do `CST` e do indicador de operação (`cIndOp`) da linha.

**Limitações conhecidas**

- A alíquota (`pAliq`) nunca é informada na DPS para município conveniado: o ADN
  toma a alíquota dos parâmetros municipais e recusa a alíquota informada em
  casos como o erro E0625.
- Empresa fora do Simples Nacional informa o tributo aproximado em `pTotTrib`;
  empresa do Simples sem faixa de receita cai no indicador `indTotTrib`, pois o
  ADN exige uma das opções.
- O grupo `IBSCBS` exporta apenas o `CST` e o `cClassTrib` da linha, com o
  `cIndOp` do indicador de operação da própria linha (herdado do produto e
  editável na linha): quem tem a classificação mas não informou o indicador nem
  o CST recebe a DPS sem o grupo, com o motivo registrado no log.
- No grupo `IBSCBS`, `finNFSe` e `indDest` saem como `"0"`: o leiaute 1.01 só
  tem `"0"` (NFS-e regular) para `finNFSe` e o `indDest = "1"` depende do grupo
  `dest`, ainda não exportado.
- CNAB e cobrança bancária não se aplicam a este módulo.
- Não existe inutilização de numeração para a NFS-e Nacional (a numeração da DPS
  é livre).

**Ainda não implementado**

- Reconciliação de resposta perdida (`GET /nfse/{chave}` e `GET /dps/{id}` antes
  de reenviar a DPS).
- Eventos de substituição (`e105xxx`) e os demais tipos de evento.
- Grupos `dest`, `gRefNFSe`, `cCredPres`, `gTribRegular` e `gDif` do `IBSCBS`.
- Distribuição de documentos recebidos, contingência e envio assíncrono com fila
  (`queue_job`).
