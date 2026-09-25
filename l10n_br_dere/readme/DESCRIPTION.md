Este módulo implementa a Onda 1 da **Declaração de Regimes Específicos
(DeRE)** brasileira, leiaute **1.2.0**.

Ele permite que uma empresa no Odoo:

- grave o regime tributário DeRE, as atividades e o plano referencial
- mapeie os campos do PGCC em `account.group` (sintético) e
  `account.account` (analítico)
- mantenha D-1001 / D-1011 e o snapshot do PGCC em um período de
  vigência da empresa, reutilizado pelas declarações mensais
- gere o XML local de D-1001, D-1011, D-1101, D-1106, D-1121, D-1198 e
  D-1199
- envie lotes assinados à Receita Integra, consulte o processamento
  (manual ou por cron com backoff) e grave protocolo, recibo e retornos
  D-9xxx
- mantenha os totais da RFB (D-9101 / D-9106 / D-9112), o retorno de
  reabertura D-9198, a apuração IBS/CBS do D-9199 e o extrato de
  vigência do D-9001 ao lado dos dados locais, sem lançar um
  `account.move`

Não implementa regras setoriais (por exemplo conciliação de
contraprestação versus taxa de administração em planos de saúde). Isso
fica nos dados da empresa ou em um módulo extra dedicado.
