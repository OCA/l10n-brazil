Como este é um módulo de infraestrutura (base abstrata), a maior parte de suas funcionalidades opera nos bastidores. No entanto, ele provê ferramentas transversais de auditoria, depuração e ações genéricas que são herdadas pelos módulos específicos (NF-e, CT-e).

## Logs de Comunicação (Auditoria e Depuração)

O módulo registra de forma detalhada todas as tentativas de comunicação com os Web Services da SEFAZ, o que é extremamente útil para diagnosticar bloqueios, erros de certificado ou instabilidades no Ambiente Nacional.

Para visualizar os logs:
1. Acesse **Configurações > Usuários e Empresas > Empresas**.
2. Abra o formulário da sua empresa.
3. Clique no botão inteligente (Smart Button) **DF-e Logs** na parte superior da tela.

Alternativamente, ative o modo desenvolvedor e acesse:
* **Faturamento > Configuração > Técnico > Logs de Distribuição DF-e**

Dentro de cada registro de log, você poderá visualizar o horário da tentativa, o resultado (Sucesso, Erro, Aviso) e as abas contendo os **XMLs brutos de Requisição e Resposta SOAP**.

## Acesso aos Payloads Brutos (XML)

Sempre que a SEFAZ retorna um documento, o arquivo zipado original é salvo no banco de dados. Para fins técnicos ou de conformidade, você pode consultar todos os fragmentos XML recebidos:

1. Com o modo desenvolvedor ativo, acesse **Faturamento > Configuração > Técnico > Payloads DF-e (Raw)**.
2. Esta tela listará todos os NSUs processados, vinculados aos seus respectivos documentos, contendo o tipo de schema (ex: `procNFe`, `resNFe`, `procCTe`, etc.) e o arquivo XML descompactado.

## Ações Globais Disponíveis

Este módulo disponibiliza ações padronizadas que podem ser utilizadas nas listagens de documentos específicos (como NF-e de Terceiros ou CT-e de Terceiros):

* **Download de XMLs (ZIP):** Selecione múltiplos documentos na listagem e acesse a engrenagem de **Ação > Download XMLs (ZIP)** para baixar um pacote contendo todos os arquivos físicos validados.
* **Vincular Parceiro:** Ação técnica para forçar o sistema a buscar e atrelar um cadastro de Parceiro (Fornecedor/Cliente) ao documento DF-e baseando-se no CNPJ/CPF contido na chave de acesso.
