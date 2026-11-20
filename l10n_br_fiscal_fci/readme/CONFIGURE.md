Os registros 0000 e 0010 do arquivo são preenchidos com os dados da
empresa: CNPJ, nome, razão social, inscrição estadual, endereço, CEP, cidade
e estado. Verifique se estão preenchidos corretamente antes de gerar um
arquivo.

A unidade de medida de uma mercadoria é informada com a abreviação da tabela
do Ato COTEPE ICMS 61/2012 (por exemplo `kg` e não `quilograma`). A
abreviação é obtida do campo *Código* da unidade de medida do produto ou,
quando ele não está na tabela, dos alias da unidade (módulo `uom_alias`),
sem diferenciar maiúsculas de minúsculas: por exemplo, o alias `UNID` da
unidade *Unidades* corresponde à abreviação `unid`. Quando nenhum deles está
na tabela é usado `99` (outras unidades). O *Código da Unidade* também pode
ser alterado em cada mercadoria.
