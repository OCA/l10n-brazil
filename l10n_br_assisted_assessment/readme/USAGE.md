Abra _Apuração Assistida > Apurações_ e crie um registro por tributo e período,
no formato `YYYY-MM`. A data de apresentação e o prazo são calculados a partir
do período e da configuração da empresa.

A rotina mensal tem três passos:

1. **Baixar** a apuração apresentada pela administração tributária, com
   _Solicitar Débitos_ e _Solicitar Créditos_. Os dois botões exigem um addon
   de transporte; sem ele, cole o arquivo na solicitação e aplique. Débitos e
   créditos são serviços separados, então uma direção que ainda não foi
   baixada (nem marcada como ausente) não gera divergência de documento só na
   escrituração.
2. **Conciliar** com o escriturado. Cada linha da apuração é casada pela chave
   de acesso a um documento fiscal autorizado e classificada como valor
   diferente, documento só na apuração, documento só na escrituração ou
   crédito não concedido. A aba _Escrituração_ lista o lado do ERP: valor
   esperado, valor do fisco e situação (aguardando download, confere, só no
   ERP ou valor diferente). Cada divergência traz a ação que a corrige, porque
   os ajustes se fazem emitindo documentos fiscais.
3. **Encerrar a revisão local**. Exige que toda divergência esteja tratada ou
   ignorada. Isso não constitui o crédito tributário nem confirma a apuração
   na RFB: o silêncio e a constituição são julgados lá. Tratar um documento
   só na apuração exige vincular o documento fiscal; ignorar exige uma nota.

Uma ação agendada diária avisa os responsáveis quando o prazo se aproxima e
marca o período como expirado depois que ele passa. A expiração local não
constitui o crédito na RFB.
