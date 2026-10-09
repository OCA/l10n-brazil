Configure a geração de faturas de retenção de impostos no Odoo seguindo estes passos:

1. **Acesse Configurações Fiscais:** Vá até `Fiscal -> Configurações -> Grupos de Impostos`. Procure por impostos retidos do tipo entrada.

2. **Configure os Impostos Retidos:** Para cada imposto que requer uma fatura de retenção, garanta que esteja corretamente configurado. Defina um fornecedor, o diário e uma conta pagável para a geração da fatura do imposto se necessário. Se um diário não for especificado, o módulo usará o diário da fatura de compra original. A conta pagável é opicional, se não definida será utilizada a conta padrão do parceiro.

3. **Definir uma Prefeitura para o ISSQN:** Crie ou edite um parceiro, vá até a aba "Fiscal" e marque a opção "É Prefeitura".

4. **Definir uma Secretaria da Fazenda estadual:** para grupos de imposto com abrangência "Estado" (ICMS e derivados), crie ou edite um parceiro da SEFAZ, informe o estado e marque a opção "É Secretaria da Fazenda Estadual". Só pode existir um parceiro assim por estado. Se nenhum for encontrado, o módulo usa o fornecedor definido no grupo de imposto.
