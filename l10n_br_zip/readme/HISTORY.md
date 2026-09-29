## 20.0.1.2.0 (2026)

O Odoo 20.0 unificou as permissões de acesso (`ir.model.access` e `ir.rule`)
no novo modelo `ir.access` e removeu os acessores `get_param`/`set_param`:

- as permissões do módulo passaram do arquivo
  `security/ir.model.access.csv` para o arquivo `security/ir.access.csv`,
  que usa o nome técnico do modelo na coluna `model_id` e a nova coluna
  `operation` (ao invés das colunas `perm_read`/`perm_write`/...);
- a leitura das configurações agora usa os acessores tipados
  (`get_int`/`get_str`) do `ir.config_parameter`;
- os ícones FontAwesome foram substituídos pelos ícones Material Symbols
  (`icon`/`data-icon`), conforme o novo padrão das views do Odoo.

## 16.0.2.0.0 (2023-06-29)

> - Biblioteca PyCEP-Correios foi renomeada para BrazilCEP.

## 16.0.1.0.0 (2022-10-25)

> - Migração para 16.0

## 15.0.1.0.0 (2022-10-25)

> - Migração para 15.0

## 14.0.1.0.0 (2022-10-25)

> - Migração para 14.0

## 12.0.3.0.0 (2021-01-08)

> - Atualizada a biblioteca pycep-correios para a versão 5.0.0
> - \[ADD\] Adicionado a opção para selecionar o provedor do serviço de
>   busca de CEP.

## 12.0.2.0.0 (2019-06-17)

> - \[REF\] Incluida pesquisa e dependência da biblioteca
>   PyCEP-Correios.
