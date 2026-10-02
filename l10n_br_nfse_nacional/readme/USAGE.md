**Emitir**

1. Crie um documento fiscal de serviço (modelo `SE`) para uma empresa
   configurada com o provedor Sefin Nacional (ADN), com tomador, linhas de
   serviço (código de serviço, impostos) e a operação fiscal.
2. Confirme o documento. O módulo monta a DPS, assina com o certificado A1 e
   valida contra o XSD. Se houver erro de schema, ele aparece no documento e
   nada é enviado; volte o documento para rascunho, corrija e confirme de novo.
3. Envie o documento. O módulo transmite a DPS ao ADN por REST/mTLS.
4. Na autorização, o documento fica **Autorizada** e guarda a chave de acesso
   de 50 dígitos, o número da NFS-e, o protocolo e o XML autorizado. Na rejeição,
   o documento fica **Rejeitada** e o motivo devolvido pelo ADN aparece no
   chatter e no evento.
5. O **DANFSe** em PDF é gerado localmente a partir do XML autorizado, pela
   ação de imprimir/gerar o PDF do documento.

**Cancelar**

1. No documento autorizado, use **Cancelar** e informe a justificativa.
2. Escolha o **código do motivo** (1 - erro na emissão, 2 - serviço não
   prestado, 9 - outros).
3. O módulo assina e envia o evento de cancelamento `101101` ao ADN e, aceito o
   evento, marca o documento como cancelado.

A inutilização de numeração não existe para a NFS-e Nacional, e por isso o botão
fica oculto nos documentos de serviço.

**Consultar o status**

Em documento autorizado, o botão **Consultar Status** pergunta ao ADN se a nota
foi cancelada por fora do Odoo (evento `101101` ou `305101`, este de ofício) e,
se foi, atualiza o documento.

**Importar XML**

O módulo importa o XML de uma NFS-e Nacional ou de uma DPS e cria o documento
fiscal correspondente.
