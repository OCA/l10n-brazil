# Monitor de NF-e (Distribuição de DFe)

Este módulo implementa a funcionalidade de monitoramento, download e processamento automático de **Notas Fiscais Eletrônicas (NF-e, modelo 55)** emitidas contra o CNPJ da sua empresa. Ele opera conectando-se diretamente ao Web Service de Distribuição de DF-e da SEFAZ (Ambiente Nacional).

Este módulo estende o framework abstrato genérico `l10n_br_fiscal_dfe` e incorpora as necessidades e especificidades exclusivas aplicadas à Nota Fiscal Eletrônica (como Manifestação do Destinatário e os schemas XML da NF-e).

## Principais Funcionalidades

* **Consulta Automática (Polling):** Tarefa agendada (Cron) que consulta periodicamente o serviço da SEFAZ, garantindo que você tenha acesso rápido a todas as NF-es emitidas contra o seu CNPJ sem precisar solicitar o arquivo ao fornecedor.
* **Processamento Especializado:** Identifica e separa os payloads baixados nos seus devidos formatos: XMLs Completos com protocolo (`procNFe`), Resumos da NF-e (`resNFe`) e Eventos da Nota Fiscal (`resEvento` / `procEventoNFe`).
* **Manifestação do Destinatário (MD-e):** Funcionalidade nativa para acusar o recebimento ou rejeição da NF-e perante a SEFAZ:
  * **Ciência da Operação:** Confirmação prévia para liberar o download do XML completo.
  * **Confirmação da Operação.**
  * **Desconhecimento da Operação.**
  * **Operação não Realizada.**
* **Manifestação Automática:** Opção para o Odoo aplicar o evento de "Ciência da Operação" instantânea e automaticamente a todas as novas notas resumidas identificadas, acelerando o recebimento do arquivo completo para importação.
* **Importação Inteligente:** Botão de ação que converte instantaneamente o XML válido baixado em um rascunho de Documento Fiscal padrão do Odoo (`l10n_br_fiscal.document`), pré-populando os impostos, CFOPs, emitentes e destinatários.
* **Geração de DANFE:** Geração do documento PDF do DANFE utilizando a biblioteca `brazilfiscalreport`.
* **Notificações:** Notifica os usuários inscritos, diretamente no inbox do Odoo, caso novas NF-es emitidas por terceiros sejam detectadas no servidor da Receita Federal.

Este módulo é implementado em estrita conformidade com a [Nota Técnica 2014.002 v1.30](https://www.nfe.fazenda.gov.br/portal/exibirArquivo.aspx?conteudo=P0U3lU1Fe40=).
