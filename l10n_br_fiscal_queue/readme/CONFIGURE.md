Em cada operação fiscal (*Fiscal / Configuração / Operações Fiscais*), o
campo **Momento da transmissão** (`queue_document_send`) define o
comportamento de envio dos documentos gerados por aquela operação:

- **Send Immediately** (padrão): transmite à SEFAZ na mesma transação
  (síncrono), preservando o comportamento original.
- **Send Later**: enfileira a transmissão como um `queue_job`, no canal
  `root.edocument`.

O `queue_job` precisa estar com o *job runner* ativo para que os jobs
enfileirados sejam processados. Consulte a documentação do `queue_job`
para configurar o runner e os canais.
