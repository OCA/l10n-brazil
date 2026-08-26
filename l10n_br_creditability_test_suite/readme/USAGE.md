## Rodar a suíte

```
odoo -d <base> -u l10n_br_creditability_test_suite --test-enable \
     --test-tags /l10n_br_creditability_test_suite --stop-after-init
```

Com `--log-level=info` cada cenário imprime um quadro do razão — esperado,
obtido e diferença por medida — **passando ou falhando**. A mesma tabela vai na
mensagem de falha. É o formato pensado para comparar checkouts lado a lado.

Exige base **com dados de demonstração**: usa a empresa
`l10n_br_base.empresa_lucro_presumido` e o plano `l10n_br_coa_generic`. Sem
isso a suíte faz `SkipTest` com a mensagem do que faltou, em vez de estourar.

Nada persiste: é `TransactionCase`. Os flips de `deductible_taxes` e as
mudanças de repartição de imposto voltam sozinhos.

## Os ciclos de demonstração

Instalar o módulo com demo cria quatro compras completas e confirmadas, que
ficam na base para inspeção na tela:

| produto | operação | CFOP | `deductible_taxes` |
|---|---|---|---|
| `DEMO-1A` | compra para revenda | 1102 | desligado |
| `DEMO-1B` | compra para revenda | 1102 | ligado |
| `DEMO-2A` | compra para uso e consumo | 1556 | desligado |
| `DEMO-2B` | compra para uso e consumo | 1556 | ligado |

Um produto por caso, para a média do AVCO não misturar as valorações.

Os ciclos nascem só na **instalação**: dados de demonstração carregam com
`noupdate=True` e o `<function>` é pulado fora do modo `init`. Para regerar numa
base já instalada:

```
odoo shell -d <base> --no-http \
  < l10n_br_creditability_test_suite/scripts/regenerate_demo_cycles.py
```

A flag `deductible_taxes` da operação é restaurada ao valor anterior no fim de
cada ciclo, inclusive em caso de erro.

## Restaurar as contas de fábrica

As contas da linha de repartição dos impostos dedutíveis são **dado**, não
código: uma migration que as altere não volta atrás ao trocar de branch. Para
medir a localização limpa:

```
odoo shell -d <base> --no-http \
  < l10n_br_creditability_test_suite/scripts/restore_stock_baseline.py
```

Lê o mapeamento do próprio plano de contas, sem código de conta escrito à mão.
