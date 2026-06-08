Este módulo é a fundação para a emissão da Nota Fiscal de Serviços Eletrônica
de padrão nacional (`NFS-e`, Sistema Nacional NFS-e) no Odoo, fornecendo uma
estrutura de dados completa e fiel ao leiaute oficial 1.00.

É importante entender que este módulo atua como uma biblioteca de modelos
abstratos (mixins) e não realiza a emissão da NFS-e por si só. Sua finalidade é
ser a base para um módulo de implementação, como o `l10n_br_nfse_nacional`, que
é responsável por mapear esses modelos nos documentos fiscais do Odoo
(`l10n_br_fiscal.document`) e comunicar-se com o ambiente nacional (Sefin
Nacional / ADN). Esta arquitetura, que separa a estrutura de dados da lógica de
emissão, é a mesma utilizada com sucesso nos outros documentos fiscais
eletrônicos da localização brasileira.

No padrão nacional, o contribuinte gera e assina uma `DPS` (Declaração de
Prestação de Serviços) e o ambiente nacional retorna a `NFS-e` autorizada, que
encapsula a DPS.

## Estrutura e Principais Conceitos da NFS-e

O módulo `l10n_br_nfse_spec` mapeia a estrutura hierárquica da DPS e da NFS-e.
Os conceitos mais importantes implementados são:

- Identificação da DPS (`infDPS`): O cabeçalho da declaração, com município
  emitente, série, número, datas e ambiente.
- Prestador e Tomador (`prest`, `toma`): Modelos para os dados cadastrais do
  prestador e do tomador do serviço, incluindo endereço nacional (`endNac`) ou
  exterior (`endExt`) e o regime de tributação (`regTrib`).
- Serviço (`serv`): O detalhamento do serviço prestado, com o local da
  prestação (`locPrest`) e a sua codificação (`cServ`): código de tributação
  nacional, código de tributação municipal e código NBS.
- Valores (`valores`): O valor do serviço (`vServPrest`), os descontos
  (`vDescCondIncond`) e a tributação — municipal/ISSQN (`tribMun`), federal e
  PIS/COFINS (`tribNac`) e o total de tributos (`tribTotal`).
- Eventos: As estruturas para os eventos da NFS-e (como o cancelamento),
  igualmente geradas a partir dos esquemas oficiais.

## Geração de Código Automatizada

A principal característica deste módulo é que 100% dos seus modelos de dados
Odoo são gerados automaticamente a partir dos esquemas XSD oficiais, publicados
pelo Sistema Nacional NFS-e. Essa geração pelo `xsdata-odoo` garante máxima
fidelidade aos leiautes fiscais e agilidade na atualização para novas versões.

Embora os esquemas XSD oficiais da NFS-e sejam publicados e mantidos pela
Receita Federal, a arquitetura deste projeto se apoia na biblioteca `nfelib`
para a tarefa de serialização dos dados em XML. Para facilitar o processo de
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

O comando utilizado para gerar os modelos da versão 1.00 da NFS-e foi:

```bash
git clone https://github.com/akretion/nfelib
cd nfelib
export XSDATA_SCHEMA=nfse
export XSDATA_VERSION=10
export XSDATA_LANG="portuguese"

xsdata generate nfelib/nfse/schemas/v1_0 \
  --package nfelib.nfse.odoo.v1_0 \
  --output=odoo

mv nfelib/odoo/nfse/v1_0 <caminho_do_odoo>/l10n_br_nfse_spec/models/v1_0
```

## Prefixo dos campos e versão

Com centenas de campos fiscais, com uma meia dúzia de documentos fiscais
complexos, com 3000 módulos OCA, existiria um risco real de conflito com os
nomes de campos vindo dos esquemas. Além disso, podemos ter várias versões da
NFS-e.

Nisso foi decidido que cada campo tem um prefixo composto do nome do schema e
de alguns dígitos da versão do esquema. No caso `nfse10_`. A escolha de 2
dígitos permite que uma atualização menor do esquema use os mesmos campos (e
dados no banco então) e que um simples update Odoo (--update=...) consiga
resolver a migração. Enquanto que para uma mudança maior de versão, seria
assumido de usar novos campos e novas tabelas (para os objetos não Odoo) e que
a lib nfelib iria trabalhar com os campos da versão maior do documento fiscal
considerado.
