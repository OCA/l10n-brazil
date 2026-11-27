Na apuração, _Solicitar Débitos_ ou _Solicitar Créditos_ abre a solicitação e
guarda o tíquete devolvido. _Solicitar Pagamentos_ e _Solicitar Recolhimentos_
fazem o mesmo para os DARFs. O restante do ciclo é automático: o callback
marca a solicitação como pronta para download, e a ação agendada baixa o
arquivo e o aplica. Débitos e créditos alimentam as linhas da apuração.
Pagamentos e recolhimentos aparecem na aba _Payments_ e no menu
_CBS Payments_, sem alterar o estado do período. O grupo apresentado pela
administração tributária mostra o andamento de cada um, como já faz para
débitos e créditos: em progresso enquanto houver solicitação aberta,
mesmo que um arquivo anterior já tenha sido aplicado, e entregue quando
essa solicitação termina.

Uma recusa deixa a solicitação no estado _Erro_, com o código e a mensagem
que voltaram, em vez de abrir um diálogo: o motivo precisa permanecer no
registro, e a chamada é cobrada pelo gateway mesmo quando recusada, então
conta na cota diária.

Quando o callback não chega, _Verificar Status_ consulta o endpoint de
status. Uma situação `CONCLUIDA` busca em seguida a URL assinada no endpoint
de download. Uma solicitação cujo processamento passou do limite de 240
minutos volta `EXPIRADA` e precisa ser aberta de novo.

A URL assinada de download vale **48 horas**. Depois disso o addon recusa o
download e é preciso uma nova solicitação. A URL autoriza o download sozinha,
por isso é guardada como segredo, restrita aos gerentes da apuração e nunca
escrita no log.

Como cada resposta só traz o que mudou desde a consulta anterior, numa janela
de no máximo 8 dias, a apuração só fica completa se as solicitações forem
abertas com regularidade. Ative a ação agendada diária, ou abra-as à mão com
frequência suficiente, e não dependa de uma única solicitação no fim do
período.
