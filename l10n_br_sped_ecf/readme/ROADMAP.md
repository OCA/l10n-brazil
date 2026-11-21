- **Assistente de encerramento do resultado.** Hoje a escrituração exige o
  lançamento de encerramento de cada período de apuração, mas não o gera: o
  usuário lança e marca à mão. Falta um assistente "encerrar o resultado do
  período" que monte e marque esse lançamento.
- **Encerramento reconhecido de outros módulos.** O `account_fiscal_year_closing`
  (repositório OCA/account-closing) marca o encerramento com `closing_type`;
  a ECF pode reconhecer essa marca também.
- **Retenção por estados, municípios e demais entes no Y570.** Os impostos
  de retenção de órgão federal já existem nos dados (6190, 6147, 6175 e
  6188, um por grupo e código). Ficam para orientação contábil os códigos
  de estados, Distrito Federal e municípios (4085, 4397, 6256), os das
  demais entidades da administração federal e os perfis de parceiro que
  apliquem essas retenções automaticamente.
- **Pontos do Y570 que dependem de orientação contábil:** o CNPJ da filial ou
  da matriz quando o cliente tem filiais (hoje vai o do parceiro da nota); o
  código do IRRF retido por estado ou município; e o ano da retenção de nota
  emitida em dezembro e paga em janeiro (hoje entra no ano da emissão).
- **Recuperação da ECD.** Quem declara contabilidade precisa recuperar a ECD
  transmitida (registro C040); o PVA aponta o erro enquanto não houver ECD
  real.
