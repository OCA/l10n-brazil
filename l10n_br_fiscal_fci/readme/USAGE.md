Acesse *Fiscal > Produto e Serviço > FCI* e crie uma nova FCI.

1. Selecione a empresa cujo estabelecimento está declarando a FCI e
   adicione uma linha por mercadoria, preenchendo o *Valor de Saída
   Interestadual* e o *Valor da Parcela Importada* por unidade de medida. O
   *Conteúdo de Importação* é calculado com a regra de arredondamento do
   manual (`ROUND(x;y)`).
2. Clique em **Gerar Arquivo**. O arquivo TXT é anexado ao registro com o
   padrão de nome `CNPJ_AAAAMMDD_hhmmss.txt` exigido pelo leiaute.
3. Baixe o arquivo e valide/transmita com o aplicativo
   *Validador/Transmissor* da SEFAZ. Informe o protocolo de recepção
   retornado pelo TED no campo *Protocolo de Recepção* e clique em
   **Confirmar Transmissão**.
4. Uma ou duas horas após a transmissão, baixe o arquivo de retorno na
   consulta restrita do sistema web da FCI ("Download Arquivo de Retorno"),
   clique em **Importar Arquivo de Retorno** e selecione o arquivo baixado
   (o TXT ou o ZIP). Os números de controle da FCI são gravados nas linhas
   de mercadorias e a FCI passa para o estado *Concluído*.

O número de controle da última FCI de um produto é exibido na aba *Fiscal*
do formulário do produto e todo o histórico fica disponível em
*Fiscal > Produto e Serviço > Mercadorias da FCI*.
