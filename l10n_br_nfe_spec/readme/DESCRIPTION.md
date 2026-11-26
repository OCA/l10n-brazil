Este módulo é a fundação para a emissão da Nota Fiscal Eletrônica (`NF-e`
modelo `55` e `NFC-e` modelo `65`) no Odoo, fornecendo uma estrutura de dados
completa e fiel ao leiaute oficial 4.0 da SEFAZ.

É importante entender que este módulo atua como uma biblioteca de modelos
abstratos (mixins) e não realiza a emissão da NF-e por si só. Sua finalidade é
ser a base para um módulo de implementação, como o `l10n_br_nfe`, que é
responsável por mapear esses modelos nos documentos fiscais do Odoo
(`l10n_br_fiscal.document`) e comunicar-se com os web services da SEFAZ. Esta
arquitetura, que separa a estrutura de dados da lógica de emissão, é a mesma
utilizada com sucesso nos outros documentos fiscais eletrônicos da localização
brasileira.

## Estrutura e Principais Conceitos da NF-e

O módulo `l10n_br_nfe_spec` mapeia com precisão a complexa estrutura
hierárquica da NF-e. Os conceitos mais importantes implementados são:

- Identificação (`ide`): O cabeçalho da nota, contendo informações como modelo,
  série, número, datas, finalidade e tipo de operação.
- Emitente e Destinatário (`emit`, `dest`): Modelos detalhados para os dados
  cadastrais completos do emissor e do recebedor da mercadoria.
- Itens da Nota (`det`): O coração da NF-e, um grupo repetível para cada
  produto ou serviço, contendo descrição, NCM, CFOP, quantidades e valores.
- Impostos (`imposto`): Dentro de cada item, há uma estrutura complexa para o
  detalhamento de todos os tributos incidentes (ICMS, IPI, PIS, COFINS, etc.).
- Totais (`total`): Contém o grupo ICMSTot com a consolidação de todas as bases
  de cálculo e valores de impostos da nota.
- Transporte (`transp`): Modelos para informar a modalidade do frete, os dados
  da transportadora, do veículo e dos volumes transportados.
- Pagamento (`pag`): Estrutura para detalhar as formas de pagamento (detPag),
  incluindo informações de cartões, PIX e boletos.

## Geração de Código Automatizada

A principal característica deste módulo é que 100% dos seus modelos de dados
Odoo são gerados automaticamente a partir dos esquemas XSD oficiais, publicados
pelo Portal da NF-e. Essa geração pelo `xsdata-odoo` garante máxima fidelidade
aos leiautes fiscais e agilidade na atualização para novas versões.

Embora os esquemas XSD oficiais da NF-e sejam publicados e mantidos no Portal
da SEFAZ, a arquitetura deste projeto se apoia na biblioteca `nfelib` para a
tarefa de serialização dos dados em XML. Para facilitar o processo de
desenvolvimento e garantir a consistência, a própria `nfelib` armazena em seu
repositório uma cópia atualizada desses esquemas oficiais.

Portanto, a prática recomendada para (re)gerar os modelos deste módulo é
utilizar um clone local do repositório da `nfelib` como fonte para os arquivos
de esquema (.xsd), direcionando o comando do `xsdata-odoo` para o diretório
correspondente.

Links:

- [GitHub - akretion/xsdata-odoo: Odoo abstract model generator from xsd schemas
  using xsdata](https://github.com/akretion/xsdata-odoo)
- [GitHub - akretion/nfelib](https://github.com/akretion/nfelib)

O comando utilizado para gerar os modelos da versão 4.0 da NF-e foi:

```bash
git clone https://github.com/akretion/nfelib
cd nfelib
export XSDATA_SCHEMA=nfe
export XSDATA_VERSION=40
export XSDATA_SKIP="^ICMS.ICMS\d+|^ICMS.ICMSSN\d+"
export XSDATA_LANG="portuguese"

xsdata generate nfelib/nfe/schemas/v4_0 \
  --package nfelib.nfe.odoo.v4_0 \
  --output=odoo

mv nfelib/odoo/nfe/v4_0 <caminho_do_odoo>/l10n_br_nfe_spec/models/v4_0
```

## Prefixo dos campos e versão

Com mais de 800 campos fiscais apenas na NF-e, com uma meia dúzia de documentos
fiscais complexos, com 3000 módulos OCA, existiria um risco real de conflito
com os nomes de campos vindo dos esquemas. Além disso, temos várias versões da
NFe, a 3.1, a 4.0 etc...

Nisso foi decidido que cada campo tem um prefixo composto do nome do schema e
de alguns dígitos da versão do esquema. No caso nfe40_. A escolha de 2 dígitos
permite que uma atualização menor do esquema use os mesmos campos (e dados no
banco então) e que um simples update Odoo (--update=...) consiga resolver a
migração. Enquanto que para uma mudança maior como de 3.1 para 4.0, seria
assumido de usar novos campos e novas tabelas (para os objetos não Odoo) e que
a lib nfelib iria trabalhar com os campos da versão maior do documento fiscal
considerado.

## O Tratamento Específico dos Impostos ICMS e ICMSSN

Um desafio particular na geração dos modelos da NF-e é a forma como o ICMS é
estruturado no XSD oficial. O esquema define um grupo de tags para cada CST de
ICMS (ex: ICMS00, ICMS10, ICMS40, etc.), muitos dos quais contêm campos com
nomes idênticos (como vBC, pICMS, vICMS).

Se todos esses grupos fossem gerados e injetados no mesmo modelo Odoo,
ocorreriam colisões de nomes de campos. Para resolver isso, o comando de
geração utiliza o parâmetro `XSDATA_SKIP` para ignorar explicitamente essas
classes de imposto individuais.

Essa abordagem é a ideal, pois a localização brasileira do Odoo, através do
módulo `l10n_br_fiscal`, já possui um sistema robusto e genérico para cálculo e
representação de impostos. Portanto, o mapeamento dos campos de impostos para
o XML é uma tarefa que exige uma lógica mais elaborada, sendo delegada ao
módulo de implementação (`l10n_br_nfe`), que é o local apropriado para tais
regras de negócio.
