## Canal queue_job

O módulo registra os jobs de distribuição DF-e no canal `root.dfe`.
É **obrigatório** configurar este canal com capacidade máxima de **1 job
simultâneo**, caso contrário consultas concorrentes à SEFAZ podem causar
erro 656 (consumo indevido) e bloqueio temporário do CNPJ.

No arquivo de configuração do Odoo:

```ini
[queue_job]
channels = root:2,root.dfe:1
```

Ou via variável de ambiente:

```
ODOO_QUEUE_JOB_CHANNELS=root:2,root.dfe:1
```

## Configuração da empresa

A configuração por empresa (ambiente, busca automática, NSU, etc.) é feita
nos módulos específicos de cada documento fiscal (ex.: aba **NF-e DF-e** do
módulo `l10n_br_nfe_dfe`).

## Notificações

Cada usuário pode ativar a preferência **DF-e Notification** em
**Preferências** para receber notificações no Inbox quando novos
documentos de terceiros forem encontrados.
