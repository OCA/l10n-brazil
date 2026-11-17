Este módulo requer os seguintes componentes e dependências para funcionar corretamente:

1. **Dependências Odoo:**
    * `l10n_br_fiscal_dfe` (O framework de distribuição abstrato da OCA)
    * `l10n_br_nfe` (O módulo base de emissão e gestão de modelos da NF-e)
    * `queue_job` (Sempre requerido pelo framework base para agendamentos e chamadas assíncronas)

2. **Dependências Python:**
    * `nfelib`: A biblioteca moderna que consolida os *bindings* e clientes de comunicação para NF-e/CT-e/MDF-e.
    * `brazilfiscalreport`: Necessária para realizar o *parse* do XML e desenhar a saída em formato PDF (DANFE).

Para instalar as bibliotecas de sistema Python:
```bash
pip install nfelib brazilfiscalreport
```

## Configuração Pré-Requisito Obrigatória

A SEFAZ bloqueia e rejeita as chamadas aos Web Services caso sua empresa não esteja perfeitamente configurada no Odoo. Antes de rodar as consultas:

1. Acesse o cadastro de **Empresas** e preencha corretamente o Estado (UF) e o **CNPJ/CPF** (somente numéricos ou formatado).
2. Na aba **Fiscal** -> **Certificados**, faça o upload e valide o **Certificado Digital A1** com a senha correta. Este certificado será utilizado ativamente pelo módulo para a troca de chaves com o Ambiente Nacional da SEFAZ.
