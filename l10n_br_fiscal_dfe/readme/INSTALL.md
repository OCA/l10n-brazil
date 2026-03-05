Este módulo atua como uma infraestrutura base (framework abstrato) e requer os seguintes componentes para funcionar:

1. **Dependências Odoo:**
    * `l10n_br_fiscal` (Framework Fiscal da OCA)
    * `queue_job` (Gerenciador de tarefas em background da OCA, necessário para o polling assíncrono)

2. **Dependências Python:**
    * `brazil_fiscal_client`: Cliente SOAP moderno e genérico utilizado para a comunicação direta com os Web Services da SEFAZ.

Para instalar a biblioteca Python necessária em seu ambiente Odoo, execute o seguinte comando:
```bash
pip install brazil-fiscal-client
```

**Nota Importante:**
Como este é apenas um módulo de motor abstrato, você raramente precisará instalá-lo diretamente de forma isolada. Ele será instalado de forma automática como dependência quando você for utilizar e instalar um dos módulos de implementação, como:

* `l10n_br_nfe_dfe` (Para o monitoramento de NF-e)
* `l10n_br_cte_dfe` (Para o monitoramento de CT-e)
