**Já implementado**

- Mapeamento da DPS sobre o documento fiscal, com prestador, tomador, serviço e
  valores, e o regime tributário (MEI, Simples Nacional ou normal) deduzido da
  empresa.
- Cliente REST/mTLS com verificação de certificado do servidor, nova tentativa
  apenas em GET e sem registrar payload nem chaves em log.
- Emissão, rejeição legível, cancelamento pelo evento `101101` e consulta de
  cancelamento feito fora do Odoo.
- DANFSe gerado do XML autorizado.

**Limitações conhecidas**

- A alíquota (`pAliq`) nunca é informada na DPS para município conveniado: o ADN
  toma a alíquota dos parâmetros municipais e recusa a alíquota informada em
  casos como o erro E0625.
- Empresa fora do Simples Nacional informa o tributo aproximado em `pTotTrib`;
  empresa do Simples sem faixa de receita cai no indicador `indTotTrib`, pois o
  ADN exige uma das opções.
- CNAB e cobrança bancária não se aplicam a este módulo.
- Não existe inutilização de numeração para a NFS-e Nacional (a numeração da DPS
  é livre).

**Ainda não implementado**

- Reconciliação de resposta perdida (`GET /nfse/{chave}` e `GET /dps/{id}` antes
  de reenviar a DPS).
- Eventos de substituição (`e105xxx`) e os demais tipos de evento.
- IBS/CBS (reforma tributária), distribuição de documentos recebidos,
  contingência e envio assíncrono com fila (`queue_job`).
