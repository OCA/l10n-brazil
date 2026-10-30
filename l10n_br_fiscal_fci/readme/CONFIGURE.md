Os registros 0000 e 0010 do arquivo são preenchidos com os dados da empresa:
CNPJ, nome, razão social, inscrição estadual, endereço, CEP, município e UF.
Confira se estão corretos antes de gerar um arquivo.

A unidade de medida da mercadoria é escrita com a abreviatura da tabela do
Ato COTEPE ICMS 61/2012 (por exemplo `kg` e não `quilograma`). A abreviatura
vem do campo *Código* da unidade de medida do produto e, se o código não
constar na tabela, usa `99` (outras unidades). O código também pode ser
alterado linha a linha.
