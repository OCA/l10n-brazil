Cada definição em *Fiscal > Configurações > E-mail de Documento Fiscal*
escolhe o modelo de e-mail por tipo de documento, emitente e situação:
autorizada, cancelada e denegada. Uma definição sem tipo de documento vale
para todos os tipos; existindo uma definição para o tipo do documento, ela
tem preferência sobre a genérica.

No cadastro do contato, o campo *E-mail de Documento Fiscal* marca quem deve
receber a notificação. Na mudança de situação, o documento passa a seguir os
contatos marcados (a própria empresa e os contatos filhos dela) e eles entram
como destinatários do e-mail, que leva o XML de autorização e a DANFE em
anexo quando esses arquivos existem.

Marcar o contato adiciona destinatários; não substitui o `partner_to` do
modelo de e-mail, que continua enviando para o parceiro do documento.
