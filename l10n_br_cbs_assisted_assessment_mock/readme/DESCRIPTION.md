Mock local da apuração assistida da CBS.

Com o modo mock ligado na empresa, abrir uma solicitação não chama a Receita
Federal. O addon responde com um tíquete local, conclui na hora e devolve um
arquivo JSON no formato dos endpoints de débitos, créditos, pagamentos e
recolhimentos. O restante do ciclo (conciliação, divergência, DARF) é o dos
addons reais.
