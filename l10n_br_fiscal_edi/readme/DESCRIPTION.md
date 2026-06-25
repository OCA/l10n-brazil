Este módulo fornece a infraestrutura base para o Intercâmbio Eletrônico de Dados (EDI)
de documentos fiscais brasileiros no Odoo.

Ele implementa uma Máquina de Estados Finitos (FSM - Finite State Machine)
para gerenciar o ciclo de vida dos documentos fiscais eletrônicos
(NF-e, NFC-e, NFS-e, CT-e, MDF-e etc.), garantindo integridade,
consistência e rastreabilidade das transições de estado.

Principais Características
--------------------------

* **Máquina de Estados (FSM):** controle rigoroso das transições de estado
  (por exemplo, de `draft` para `open`, depois para `sending` e finalmente
  para `authorized`, `rejected` ou `denied`), com bloqueio de movimentos
  inválidos.
* **Configuração extensível por documento:** a FSM base é definida no método
  `get_state_machine_config()` e pode ser sobrescrita por módulos específicos
  de documento fiscal para ajustar estados, transições e callbacks.
* **Gerenciamento de Eventos:** arquitetura para suportar eventos fiscais
  vinculados ao documento, como Cancelamento, Carta de Correção Eletrônica
  (CC-e) e Inutilização de Numeração.
* **Abstração de Protocolo:** separa a lógica de negócios da lógica de
  comunicação. Módulos específicos (como `l10n_br_nfe` ou `l10n_br_nfse`)
  herdam deste módulo para implementar a integração com webservices
  (SEFAZ/Prefeituras), enquanto o `l10n_br_fiscal_edi` orquestra o fluxo.
* **Interface Padronizada:** oferece uma experiência consistente com botões e
  ações uniformes, independentemente do modelo de documento fiscal.

Workflow de Estados
-------------------

O diagrama abaixo ilustra os estados e transições padrão definidos no módulo
base (a configuração pode ser estendida/sobrescrita por módulos filhos):

![FSM state diagram](static/description/fsm_graph.png)
