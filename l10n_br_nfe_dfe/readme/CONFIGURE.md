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

Em **Faturamento > Configuração > Empresas**, na aba **Fiscal > DF-e**
(Configurações DF-e):

- **Versão DF-e**: versão do serviço (padrão: 1.01)
- **Ambiente DF-e**: Produção ou Homologação
- **Busca automática de DF-e**: habilita a consulta automática via cron
- **Manifestação Automática do Destinatário (NF-e)**: envia ciência da
  operação automaticamente para cada resumo de NF-e recebido

A empresa precisa ter um **certificado digital A1** configurado no módulo
`l10n_br_fiscal_certificate`.

## Notificação de documentos (por usuário)

Em **Preferências do Usuário**, o campo **Notificação DF-e** habilita o
recebimento de notificações na caixa de entrada quando novos documentos de
terceiros são encontrados pela distribuição DF-e.
