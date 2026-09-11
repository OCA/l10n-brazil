## Configuração

Para habilitar a busca e o processamento automático de notas:
1. Acesse **Configurações > Usuários e Empresas > Empresas**.
2. Abra o cadastro da sua empresa e localize a aba ou seção **NF-e DF-e**.
3. Marque a opção **Auto-fetch NF-e** para que o Odoo realize as consultas periódicas de forma agendada em background.
4. Opcionalmente, ative a **Manifestação Automática** caso queira que o sistema registre o evento de "Ciência da Operação" automaticamente assim que a SEFAZ alertar sobre a existência de uma nota nova. Isso acelera significativamente a liberação do XML completo para download.

## Painel de Controle (Dashboard)

Acesse a visão principal navegando por **Faturamento > Fiscal > Consultas DF-e > NF-e de Terceiros**.

No topo da listagem, o sistema exibe um painel de status em tempo real da sua comunicação com a SEFAZ:
* **Status do Ambiente:** Indica se você está operando em Produção ou Homologação.
* **Progresso do NSU:** Mostra a numeração em que o seu Odoo está (Último NSU) comparado ao NSU máximo registrado na base da Receita Federal para o seu CNPJ. Quando os números se igualam, a tag verde "Sincronizado" é exibida.
* **Importações Pendentes:** Um contador de alerta que mostra quantas notas completas já foram baixadas em XML, mas ainda não foram efetivamente importadas como Documentos Fiscais no Odoo.

## Fluxo de Trabalho e Ações Disponíveis

Ao clicar em um documento na listagem, você poderá identificar a sua situação através das cores (Azul para Resumo, Verde para XML Completo). O fluxo padrão permite as seguintes ações:

1. **Manifestar:** Botão que abre o assistente para você enviar oficialmente um evento à SEFAZ (Ciência, Confirmação, Desconhecimento ou Operação Não Realizada). Lembre-se: por regras da SEFAZ, o XML completo com validade jurídica (`procNFe`) só é liberado para download após uma manifestação de Ciência ou Confirmação.
2. **Importar como Documento Fiscal:** Disponível apenas quando o XML completo já foi baixado. Este botão converte o XML imediatamente em um registro de `l10n_br_fiscal.document`, preenchendo automaticamente os fornecedores, CFOPs e valores para uso nos módulos de compras e estoque.
3. **Download PDF:** Utiliza os dados do XML para gerar e baixar o arquivo PDF do DANFE.
4. **Pesquisa Específica:** No painel superior das listagens, você encontra o assistente de busca específica. Ele permite pular o sequencial de NSU e forçar a requisição pontual de uma NF-e utilizando apenas a sua **Chave de Acesso** (44 dígitos), ideal para notas de recebimento urgente.
