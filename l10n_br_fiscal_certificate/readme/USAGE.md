## Cadastro do certificado

1. Importe o certificado A1 (arquivo `.pfx` ou `.p12`) em
   **Fiscal > Configuração > Outros > Certificados**, informando a senha do
   arquivo. Para empresas brasileiras o campo "Scope" já vem preenchido com
   "Brazilian Fiscal".
2. Na ficha da empresa (**Configurações > Empresas**), aba **Fiscal**, página
   **Certificados**, escolha o certificado no campo **Certificado**
   (`certificate_id`). O certificado também pode ser criado direto por esse
   campo.

Cada empresa usa um único certificado. Uma filial sem certificado próprio usa
o certificado da matriz: nesse caso, o campo **Certificate in Use**
(`certificate`, somente leitura) mostra o certificado que será utilizado.

## Uso

O certificado é usado automaticamente para assinar e transmitir os documentos
fiscais eletrônicos (NF-e, NFC-e e NFS-e), para os eventos de manifestação do
destinatário e a inutilização de numeração (NF-e) e para a distribuição de
DF-e. Não é preciso configurar nada nos módulos de cada documento.

A validade é conferida a cada uso: um certificado vencido impede a assinatura
e a transmissão, com uma mensagem de erro indicando o período de validade do
certificado.

Para renovar, importe o novo certificado e troque o campo **Certificado** da
empresa.

## Alerta de expiração

Em **Configurações**, o campo **Alerta de Certificado Expirado** define a
antecedência, em dias, do alerta de expiração do certificado (padrão: 30
dias).
