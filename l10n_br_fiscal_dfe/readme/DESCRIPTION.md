# Framework Base para Distribuição de Documentos Fiscais Eletrônicos (DF-e)

Este módulo serve como um **framework abstrato** para o monitoramento e download de documentos fiscais eletrônicos (DF-e) disponibilizados pela SEFAZ através dos Web Services de Distribuição (Ambiente Nacional).

**Atenção:** Este módulo não realiza consultas de documentos específicos por si só. Ele fornece a infraestrutura técnica e comum para que módulos de implementação realizem o trabalho, como:

*   `l10n_br_nfe_dfe`: Para Nota Fiscal Eletrônica (NF-e - Modelo 55).
*   `l10n_br_cte_dfe`: Para Conhecimento de Transporte Eletrônico (CT-e - Modelo 57).

## Principais Funcionalidades da Base

Ao isolar a lógica de comunicação com a SEFAZ, este módulo previne a duplicação de código e garante um comportamento padronizado na localização brasileira do Odoo. Ele fornece:

*   **Motor de Consulta Genérico:** Lógica de loop de consulta, paginação de NSUs (Número Sequencial Único) e integração com o `queue_job` para processamento assíncrono em background.
*   **Gerenciamento de Cooldown:** Tratamento inteligente de pausas e bloqueios para evitar punições da SEFAZ, lidando automaticamente com os códigos de status 137 (Nenhum documento) e 656 (Consumo Indevido).
*   **Armazenamento de XML:** Estrutura de dados (`l10n_br_fiscal_dfe.dfe`) para armazenar nativamente os payloads XML compactados em Base64/gZip retornados pela SEFAZ (`docZip`).
*   **Cabeçalho de Documento Unificado:** Modelo genérico (`l10n_br_fiscal_dfe.document`) para agrupar os XMLs e armazenar metadados comuns (Chave de Acesso, Emitente, Valor, Data, CNPJ) independente do tipo de documento fiscal.
*   **Logs de Comunicação SOAP:** Sistema robusto de log de auditoria (`l10n_br_fiscal_dfe.distribution_log`) que grava integralmente as requisições e respostas XML brutas para depuração.
*   **Interface de Usuário Comum:** Estruturas base para o painel de status (Banner), vistas de lista, formulários e assistentes (*wizards*) de busca específica (por Chave de Acesso ou NSU).
*   **Utilitários Compartilhados:** Ferramentas para descompactação de XMLs, validação de chaves de acesso, vinculação automática de Parceiros (via CNPJ/CPF) e download em lote (ZIP).
