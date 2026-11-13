## Dependências Python

- `erpbrasil.base` — validação de chave de acesso (dígito verificador)

Os módulos específicos declaram suas próprias dependências (ex.:
`l10n_br_nfe_dfe` requer `nfelib` e `brazilfiscalreport`).

## queue_job como server wide module

O `queue_job` precisa ser carregado na inicialização do Odoo. Adicione na
configuração do servidor:

```ini
[options]
server_wide_modules = web,queue_job
```

Ou via variável de ambiente:

```
SERVER_WIDE_MODULES=web,queue_job
```

Em produção, o Odoo deve rodar com `workers > 0` para que o jobrunner
inicie como processo dedicado.

Com `--workers=0` (modo threaded / desenvolvimento), o queue_job funciona
normalmente — ele cria uma thread extra no mesmo processo.
