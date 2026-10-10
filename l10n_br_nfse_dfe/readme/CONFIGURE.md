## Canal queue_job

A distribuição reutiliza o canal `root.dfe` já registrado por `l10n_br_fiscal_dfe`. Mantenha a capacidade desse canal em **1 job simultâneo** para não disparar o limite de requisições do ADN (HTTP 429).

```ini
[queue_job]
channels = root:2,root.dfe:1
```

## Empresa

Em **Faturamento > Configuração > Empresas**, aba **Fiscal > NFS-e DF-e**:

* **Ambiente ADN**: Produção ou Produção restrita. O padrão é produção restrita. Este campo não é o ambiente `1`/`2` da emissão municipal.
* **Busca automática**: liga o cron que chama `_cron_dfe_search_documents('nfse')`.
* **Produto padrão de importação**: produto de serviço preenchido no assistente quando a NFS-e é importada.
* **Último NSU**: cursor da próxima consulta. Pode ser ajustado para reprocessar a partir de um ponto.

O certificado e-CNPJ fica na configuração fiscal já existente.
