Acesse *Fiscal > Produto e Serviço > FCI* e crie uma nova FCI.

1. Selecione a empresa cujo estabelecimento está declarando a FCI e inclua uma
   linha por mercadoria, informando o *Valor de Saída Interestadual* e o
   *Valor da Parcela Importada* por unidade de medida. O *Conteúdo de
   Importação* é calculado com a regra de arredondamento do manual
   (`ROUND(x;y)`).
2. Clique em **Gerar Arquivo**. O arquivo TXT é anexado ao registro com o nome
   no padrão `CNPJ_AAAAMMDD_hhmmss.txt` exigido pelo leiaute.
3. Baixe o arquivo e valide/transmita com o aplicativo *Validador/Transmissor*
   da SEFAZ. Informe o protocolo de recepção devolvido pelo TED no campo
   *Protocolo de Recepção* e clique em **Confirmar Transmissão**.
4. Uma ou duas horas depois da transmissão, baixe o arquivo de retorno na
   consulta restrita do sistema FCI na web (*Download Arquivo de Retorno*),
   clique em **Importar Arquivo de Retorno** e selecione o arquivo baixado
   (o TXT ou o ZIP). Os números de controle da FCI são gravados nas linhas
   de mercadoria e a FCI passa para concluída.

O número de controle da última FCI de um produto aparece na aba *Fiscal* do
formulário do produto, e o histórico completo está em *Fiscal > Produto e
Serviço > Mercadorias da FCI*.
