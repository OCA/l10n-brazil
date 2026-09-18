Ao confirmar e enviar um documento fiscal cuja operação está configurada
como **Send Later**, a transmissão à SEFAZ é enfileirada em vez de
executada na hora. O documento permanece no estado *Aguardando envio*
até que o job seja processado pelo `queue_job`; concluída a transmissão,
o estado avança normalmente (autorizada, rejeitada, etc.), como no envio
síncrono.

Os jobs enfileirados podem ser acompanhados em *Job Queue / Jobs*, no
canal `root.edocument`.
