Na apuração, _Solicitar Débitos_ ou _Solicitar Créditos_ abre a solicitação e
guarda o tíquete devolvido. O restante do ciclo é automático: o callback
marca a solicitação como pronta para download, e a ação agendada baixa o
arquivo e o aplica aos períodos que ele carrega.

Uma recusa deixa a solicitação no estado _Erro_, com o código e a mensagem
que voltaram, em vez de abrir um diálogo: o motivo precisa permanecer no
registro, e a chamada é cobrada pelo gateway mesmo quando recusada, então
conta na cota diária.

Quando o callback não chega, _Verificar Status_ consulta o endpoint de
status. Uma solicitação cujo processamento passou do limite de 240 minutos
volta com erro e precisa ser aberta de novo.

A URL assinada de download vale **48 horas**. Depois disso o addon recusa o
download e é preciso uma nova solicitação. A URL autoriza o download sozinha,
por isso é guardada como segredo, restrita aos gerentes da apuração e nunca
escrita no log.

Como cada resposta só traz o que mudou desde a consulta anterior, numa janela
de no máximo 8 dias, a apuração só fica completa se as solicitações forem
abertas com regularidade. Ative a ação agendada diária, ou abra-as à mão com
frequência suficiente, e não dependa de uma única solicitação no fim do
período.
