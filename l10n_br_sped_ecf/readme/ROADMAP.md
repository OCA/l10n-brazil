- **Assistente de encerramento do resultado.** Hoje a escrituração exige o
  lançamento de encerramento de cada período de apuração, mas não o gera: o
  usuário lança e marca à mão. Falta um assistente "encerrar o resultado do
  período" que monte e marque esse lançamento.
- **Encerramento reconhecido de outros módulos.** O `account_fiscal_year_closing`
  (repositório OCA/account-closing) marca o encerramento com `closing_type`;
  a ECF pode reconhecer essa marca também.
- **Retenção por órgão federal no Y570.** O gerador já agrupa o IRPJ e a CSLL
  retidos por órgão federal numa linha só (código 6190 ou 6147), mas os dados
  ainda não têm os impostos de retenção de órgão federal.
- **Pontos do Y570 que dependem de orientação contábil:** o CNPJ da filial ou
  da matriz quando o cliente tem filiais (hoje vai o do parceiro da nota); o
  código do IRRF retido por estado ou município; e o ano da retenção de nota
  emitida em dezembro e paga em janeiro (hoje entra no ano da emissão).
- **Recuperação da ECD.** Quem declara contabilidade precisa recuperar a ECD
  transmitida (registro C040); o PVA aponta o erro enquanto não houver ECD
  real.
