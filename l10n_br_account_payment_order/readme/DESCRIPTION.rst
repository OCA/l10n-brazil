O módulo implementa a parte comum da infra-estrutura necessária para o uso do CNAB implementando:

- **Códigos CNAB** - códigos de Instrução, Retorno, Carteira e Desconto.

- **Configuração CNAB** - onde serão salvas as informações específicas de cada caso como Convênio, Código do Beneficiário, Modalidade, Percentual de Multa, códigos de Instrução do Movimento de Liquidação de Alteração de Vencimento e etc.

- **Modo de Pagamento** - localiza o módulo `account_payment_mode <https://github.com/OCA/bank-payment/tree/14.0/account_payment_mode>`_ para associar o **Diário Contábil** referente a **Conta Bancária** do CNAB e informar a **Configuração do CNAB** que será usada, assim ao informar o Modo de Pagamento em um Pedido de Venda, Compras ou Faturamento o programa identifica como sendo um caso CNAB.

- **Ordem de Pagamento** - localiza o módulo `account_payment_order <https://github.com/OCA/bank-payment/tree/14.0/account_payment_order>`_ que usa a **Ordem de Pagamento**, débito ou crédito, para registrar as **Instruções de Movimento** e onde será criado o **Arquivo CNAB Remessa**.

- **Registro do LOG de Eventos** - ao importar um arquivo de retorno CNAB.

- **Grupos e Permissões de acesso** - CNAB Usuário e Gerente.

A implementação foi pensada para permitir que seja possível usar diferentes Bibliotecas para **Gerar os Boletos, Arquivo CNAB de Remessa e tratar o Arquivo de Retorno do CNAB** por isso é preciso instalar um segundo módulo que vai ter essa função, portanto a ideia é que nesse módulo deverá estar tudo que for comum para a implementação mas o CNAB não irá funcionar sem esse segundo módulo.

**IMPORTANTE:** Apesar de muitas Documentações do CNAB acabarem dizendo que usam o "Padrão FEBRABAN" na realidade e ao longo dos anos foi visto que existem muitas divergências entre os casos incluindo diferentes Códigos para a mesma função ou mesmo Termos e nomenclaturas que apesar de semelhantes podem acabar confundindo o usuário, por isso essa falta de padrão foi considerada na implementação e na arquitetura do módulo e também precisa ser considerada em manutenções, melhorias ou no uso de outras Bibliotecas, é preciso separar o que é realmente comum do que pode variar entre os Bancos e CNAB, nesse sentido foram incluídos nos Dados de Demonstração mais de um caso para ficar claro aos desenvolvedores essas particularidades e evitar uma arquitetura que desconsidere esse aspecto.
