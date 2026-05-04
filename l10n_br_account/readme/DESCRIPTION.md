# Visão Geral

O módulo `l10n_br_account` integra o motor fiscal brasileiro (`l10n_br_fiscal`) ao framework contábil nativo do Odoo (módulo `account`). Ele integra a complexa lógica da tributação e dos documentos fiscais do Brasil com as faturas e lançamentos contábeis conforme as normas de contabilidade brasileiras.

O módulo atende desde a automação na emissão de notas para empresas do Simples Nacional até os cenários contábeis mais exigentes do regime normal (Lucro Real/Presumido).

# Arquitetura e Integração: Decorator Pattern (`_inherits`)

A arquitetura do módulo se baseia no mecanismo de herança por composição `_inherits` do Odoo para criar uma composição dinâmica entre os modelos fiscais e contábeis:

*   **account.move** herda de **l10n_br_fiscal.document**
*   **account.move.line** herda de **l10n_br_fiscal.document.line**

Esta abordagem, análoga ao *Decorator Pattern*, oferece as seguintes vantagens:

1.  **Gerenciamento Unificado**: Permite controlar o Documento Fiscal diretamente pela interface da Fatura do Odoo. Campos fiscais (CFOP, NCM, valores de impostos) são acessados e computados de forma transparente, como se fossem nativos do `account.move.line`.

2.  **Baixíssima Redundância de Dados**: A herança por composição evita a duplicação de centenas de campos fiscais nas tabelas contábeis. A "fonte da verdade" fiscal é sempre o registro em `l10n_br_fiscal.document`, garantindo um banco de dados normalizado e consistente.

3.  **Modularidade e Manutenção**: A lógica fiscal complexa permanece encapsulada no `l10n_br_fiscal`. Para assegurar a reatividade dos campos computados na interface da fatura, o módulo utiliza um *mixin* especializado (`l10n_br_account.decorator.mixin`) que gerencia a herança de métodos e campos dinâmicos.

# Principais Funcionalidades e Casos de Uso

# Uso Simplificado: Cálculo dos impostos e criação dos Documentos Fiscais

O módulo `l10n_br_account` é a peça chave para automatizar a emissão de documentos fiscais a partir de qualquer fluxo de negócio que gere uma fatura no Odoo, como:
*   Ordens de Venda (`sale.order`)
*   Ordens de Compra (`purchase.order`)
*   Movimentações de Estoque (`stock.picking`)
*   Contratos (`contract.contract`), entre outros.

A **Operação Fiscal** pré-configurada orquestra o preenchimento automático de todos os dados necessários, permitindo a geração de NF-e, NFS-e e outros documentos com mínima intervenção.

# Uso Avançado: Lançamentos contábeis corretos para as empresas do Regime Normal

Para empresas no Lucro Real ou Presumido, o `l10n_br_account` habilita uma gestão contábil e fiscal precisa e aderente à legislação.

*   **Lançamentos Contábeis de Impostos**: Conecta os impostos fiscais (`l10n_br_fiscal.tax`) aos contábeis (`account.tax`), garantindo que a validação de uma fatura gere os lançamentos corretos para ICMS, IPI, PIS, COFINS, etc., em suas respectivas contas (custo, recuperável, despesa).

*   **Operações Sem Impacto Financeiro**: Suporta operações como "Remessa para Industrialização", permitindo a emissão do documento fiscal obrigatório e o lançamento correto dos impostos, mas sem gerar contas a pagar ou a receber, mantendo a integridade fiscal e contábil.

*   **Composição de Valores Financeiros**: Gerencia a correta composição do valor financeiro das faturas. Por exemplo, assegura que o valor do IPI, quando não recuperável, seja somado ao contas a pagar do fornecedor.

*   **Importação de Documentos (XML)**: Facilita a importação de documentos de fornecedores, criando simultaneamente o `l10n_br_fiscal.document` com os dados fiscais e a fatura de fornecedor (`account.move`) pronta para validação e pagamento.

# Escopo e Delimitação do Módulo

O nome `l10n_br_account` deriva do módulo `account`, que ele estende. É importante notar que o módulo `account` do Odoo, em sua essência, é focado em faturamento, embora contenha os conceitos fundamentais de planos de contas e lançamentos contábeis.

Para uma contabilidade completa de uma empresa no regime normal, mesmo utilizando o Odoo Enterprise, é necessária a instalação de dezenas de módulos adicionais da OCA, provenientes de diversos repositórios da OCA. O `l10n_br_account`, apesar do nome, **não substitui** este ecossistema. Ele se concentra na ponte fiscal-contábil. Funções como conciliação avançada (através de módulos como `account_reconcile`), gestão de ordens de pagamento, integração bancária (CNAB) e importação de extratos são tratadas por dezenas de outros módulos específicos da OCA...

Por outro lado, é importante ressaltar que os autores deste módulo possuem clientes do regime normal com uma contabilidade significativamente mais completa do que a oferecida nativamente pelo Odoo Enterprise, baseando-se exclusivamente em módulos de código aberto da OCA. Alcançar tal nível de sofisticação, no entanto, exige anos de experiência em implementação e uma escolha estratégica da versão do Odoo. É importante evitar versões muito recentes, para as quais o ecossistema de módulos da OCA ainda não atingiu a maturidade e estabilidade necessárias após o processo de migração (uma versão nova do Odoo mal tem 500 módulos da OCA migrados depois de 6 meses, mas tem quase 2000 depois de um ano e quase 3000 depois de 3 anos).

Vale a pena mencionar que lançamentos de Custo da Mercadoria Vendida (CMV) e outros lançamentos de contabilidade de estoque IFRS/IAS2, são tipicamente realizados através da combinação do módulo nativo `stock_account`, do `l10n_br_stock_account` (deste mesmo repo) e da ativação do modo "anglo-saxon" no seu plano de contas.

# Detalhes sobre o modelo de dados

# Cardinalidade: Documentos Fiscais e Lançamentos Contábeis

A arquitetura suporta cenários onde um único lançamento financeiro (`account.move`) agrupa múltiplos documentos fiscais, como uma fatura única para pagar vários Conhecimentos de Transporte (CT-e). Esta flexibilidade é garantida por três campos-chave:

*   **account.move.fiscal_document_id**: O campo `Many2one` que implementa o `_inherits`. Representa o documento fiscal "principal" ou em edição na interface da fatura.

*   **account.move.line.fiscal_document_line_id**: O pilar da arquitetura. Permite que **cada linha** da fatura aponte para uma linha de um documento fiscal distinto. É isso que possibilita agregar múltiplos documentos em um único `account.move`.

*   **account.move.fiscal_document_ids**: Campo `One2many` computado que agrega todos os documentos fiscais vinculados às linhas da fatura, oferecendo uma visão completa e consolidada quando o lançamento tem mais de um documento fiscal.

A flexibilidade do design é bidirecional. O sistema também gerencia nativamente cenários onde **um lançamento contábil (`account.move`) não possui nenhum documento fiscal associado**. Isso é fundamental para operações puramente contábeis ou não fiscais, como:
*   Lançamentos de folha de pagamento.
*   Operações financeiras ou contábeis em empresas de um grupo multinacional que não operam no Brasil.

Além disso, mesmo dentro de uma fatura fiscalizada, a associação é granular. Apenas as linhas de produto (`invoice_line_ids` com `display_type='product'`) são vinculadas a uma `l10n_br_fiscal.document.line`. Linhas de impostos, de contas a pagar/receber, ou linhas de anotação/seção permanecem como lançamentos puramente contábeis, sem linha de documento fiscal específica.

# Observação sobre a Normalização do Modelo de Dados

Idealmente, o modelo de dados teria redundância zero. Contudo, para simplificar a injeção de mixins fiscais — em especial o `l10n_br_fiscal.document.line.mixin` — e alavancar a lógica nativa do Odoo, foi uma decisão de design manter a nomenclatura de um pequeno e controlado conjunto de campos, como `partner_id`, `company_id`, `user_id`, `currency_id`, `product_id`, `quantity`, `price_unit` e `name`.

Como consequência, existe uma redundância mínima e gerenciada. Considerando os milhares de campos necessários para a diversidade de documentos fiscais brasileiros, apenas cerca de quatro campos do `account.move` e quatro do `account.move.line` são efetivamente duplicados. Para garantir a integridade, estes campos (apelidados de *shadow fields*) são cuidadosamente sincronizados em tempo real, inclusive durante a edição de novos registros em memória (fase `NewId`), assegurando total consistência entre a fatura e o documento fiscal.

# A Separação Estratégica dos Mixins Fiscais

No caso do `account.move`, o objetivo era obter os campos do `l10n_br_fiscal.document` sem duplicá-los (o que o `_inherits` faz perfeitamente), mas também precisávamos de seus métodos (como `_compute_fiscal_tax_ids` ou `_compute_tax_fields`). Se usássemos `_inherit` no mixin principal (`l10n_br_fiscal.document.mixin`), teríamos os métodos, mas os campos seriam duplicados, quebrando o princípio de normalização.

Por outro lado, modelos como `sale.order` e `purchase.order` não são uma representação de um documento fiscal, mas sim precursores dele. Portanto, eles podem usar uma herança simples (`_inherit`) diretamente no mixin principal (`l10n_br_fiscal.document.mixin`), pois precisam tanto dos campos quanto dos métodos para preparar os dados que serão posteriormente utilizados na geração do documento fiscal.

# Modelo UML Simplificado

![UML account.move](../static/img/account_move.png)

![UML account.move.line](../static/img/account_move_line.png)

# Aviso Importante: Pré-requisitos e Complexidade

Para utilizar o `l10n_br_account` de forma eficaz, é necessário ter domínio aprofundado de dois ecossistemas complexos: o módulo `account` nativo do Odoo e o motor `l10n_br_fiscal` deste repositório.

O `account` é o maior e mais intrincado módulo do Odoo, constituindo por si só um ERP financeiro completo, e não apenas um simples software de emissão de notas para microempresas. Por sua vez, o `l10n_br_fiscal` é o maior módulo entre os mais de 3000 disponíveis na OCA. Este módulo, `l10n_br_account`, está também entre os três mais complexos da localização brasileira e exige um uso avançado do ORM do Odoo para gerenciar a dualidade documento fiscal/lançamento contábil.

A implementação bem-sucedida de um ERP estrangeiro no Brasil é uma tarefa que demanda profissionais altamente qualificados, com anos de experiência em programação backend (Python) e implantação de verdadeiros sistemas ERP. Uma implementação não se resume a baixar e instalar módulo (apenas 1% do trabalho); envolve análise de processos, configuração, migração de dados e customizações, migração de modulos OCA a partir de outras versões... Subestimar essa complexidade invariavelmente leva a projetos problemáticos e custos elevados no longo prazo.

Este aviso serve para alinhar expectativas e reforçar que o sucesso de uma implantação Odoo no Brasil depende de expertise técnica e funcional aprofundada. Infelizmente, este mercado atrai aventureiros que subestimam essa complexidade ou que vendem projetos acreditando ser possível terceirizar a execução sem grande compromisso com a entrega, explorando a falta de informação do cliente. Este cenário caracteriza um "market for lemons", onde a assimetria de informação torna difícil distinguir entre fornecedores qualificados e despreparados, impedindo o desenvolvimento de um mercado de implementação maduro.

Agravando a situação, onde se esperaria uma garantia criteriosa de qualidade, o ecossistema corporativo "oficial" investe pesadamente em propaganda para mascarar essa realidade, promovendo uma visão onde a consultoria de implementação é tratada como uma commodity. Esse modelo, focado em comissões pela venda de licenças (muitas vezes desnecessárias ao utilizar o ecossistema da OCA), alimenta um mercado paralelo notório de "parceiros fantoches/bucha de canhão" que compram certificações oficiais de empresas estrangeiras para simular uma competência que não possuem. Cuidado com profissionais que ostentam certificações compradas para transferir a responsabilidade da implementação sem o devido suporte ou conhecimento real. Não se deixe enganar por narrativas que simplificam a complexidade do projeto para priorizar a venda de licenças!

# Conclusão

O `l10n_br_account` possui um design robusto que unifica as complexas lógicas fiscal e contábil do Brasil dentro do Odoo. Sua arquitetura, projetada por especialistas para especialistas, oferece uma plataforma flexível e confiável, capaz de sustentar operações de alta complexidade e garantir a conformidade fiscal e contábil das empresas que utilizam a localização brasileira da OCA.
