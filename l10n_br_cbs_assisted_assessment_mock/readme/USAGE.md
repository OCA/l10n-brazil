No período CBS, o gerente da apuração liga *CBS Mock* logo abaixo do título.
A mesma chave fica na empresa, aba *Assisted Assessment*. Só um gerente muda
essa chave. Com ela ligada, o período mostra um aviso de que nada é enviado
à Receita.

*Prepare Mock Files*, no período ou no menu, grava um arquivo por serviço a
partir dos documentos fiscais autorizados daquele mês. Saídas viram débitos,
entradas viram créditos, e os pagamentos trazem um DARF RAD e um PCONT. Sem
documento no período, o arquivo leva uma linha de exemplo.

A solicitação seguinte daquele serviço consome o arquivo preparado. Se não
houver arquivo esperando, a abertura monta um para o mês corrente. *Verificar
Status* conclui na hora e *Download* aplica o JSON, como no transporte real.
