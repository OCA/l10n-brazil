O fluxo operacional para emissão e gerenciamento de documentos fiscais
(eletrônicos e não eletrônicos) segue as etapas abaixo.

1. Validação (`draft` -> `open`)
--------------------------------

* O documento inicia no estado **Rascunho** (`draft`).
* Ao clicar no botão **Confirmar**, o sistema executa validações de
  integridade, define data, comentário, numeração/sequência (quando aplicável)
  e demais preparações do documento.
* O estado muda para **Em Aberto** (`open`), indicando que o documento está
  apto para o próximo passo.

2. Transmissão (`open` -> `sending` -> resultado)
-------------------------------------------------

* No estado **Em Aberto**, o botão **Enviar** fica disponível.
* Ao enviar, o documento vai para o estado transitório **Enviando**
  (`sending`), e a camada de integração executa a comunicação com o fisco.
* Possíveis resultados padrão:

  * **Autorizado** (`authorized`): autorização concluída com protocolo e XML
    de retorno.
  * **Rejeitado** (`rejected`): erros de validação retornados pelo fisco.
    O usuário corrige o documento e pode enviar novamente.
  * **Denegado** (`denied`): irregularidade fiscal. Em geral, representa um
    estado final para aquela numeração.

* Observação: para documentos não eletrônicos (ou sem processador), o fluxo de
  envio pode finalizar diretamente em **Autorizado** conforme a implementação.

3. Cancelamento (`*` -> `cancel`)
---------------------------------

* O estado **Cancelado** (`cancel`) pode ser atingido a partir de múltiplos
  estados no fluxo base (`authorized`, `open`, `rejected`, `draft`, `sending`).
* Para documentos autorizados eletrônicos emitidos pela empresa, a ação de
  cancelar abre assistente próprio para coleta/processamento da justificativa.
* Para documentos ainda não autorizados, o cancelamento pode ocorrer
  diretamente no fluxo local.

4. Retorno para Rascunho (`*` -> `draft`)
-----------------------------------------

* O fluxo base permite retornar para **Rascunho** (`draft`) a partir de
  `open`, `sending`, `rejected`, `cancel`, `denied` e também de `draft`
  (idempotente).
* Essa ação limpa informações transitórias de erro/relatório para permitir
  nova preparação do documento.

5. Eventos e correções
----------------------

* **Carta de Correção (CC-e):** para documentos autorizados que suportam o
  evento.
* **Inutilização de Numeração:** para faixas de numeração não utilizadas,
  conforme regras fiscais aplicáveis.

6. Extensão do workflow por módulo fiscal
-----------------------------------------

A FSM deste módulo é projetada para extensão. Módulos de tipos fiscais
específicos podem sobrescrever `get_state_machine_config()` e callbacks
relacionados para:

* incluir estados adicionais;
* alterar transições válidas;
* personalizar regras de pré/pós-transição;
* adaptar o fluxo ao comportamento dos webservices de cada documento.
