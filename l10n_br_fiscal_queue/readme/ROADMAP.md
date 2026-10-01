- Enfileirar também a consulta de status do documento. Hoje ela é
  síncrona: quando a API do provedor (por exemplo, a Focus, na NFS-e)
  está lenta ou indisponível, cada clique em *Verificar Status* prende um
  worker HTTP, como o envio prendia antes deste módulo. A proposta é uma
  opção na operação fiscal, `queue_status_check`, com os modos sem
  verificação, síncrona, enfileirada (`queue_job`, com novas tentativas
  em falha de rede) e automática por cron para os documentos pendentes.
  Será feita em PR separado.
