Este módulo é a fundação para a emissão do Conhecimento de Transporte
Eletrônico (`CT-e`, `Modelo 57`) no Odoo. Ele fornece a estrutura de dados
completa e atualizada, em conformidade com os leiautes oficiais da SEFAZ para
o CT-e 4.0.

É importante ressaltar que este módulo não realiza a emissão do CT-e sozinho.
Ele funciona como uma biblioteca de modelos de dados abstratos (mixins). A sua
principal função é servir de base para um módulo de implementação, como o
`l10n_br_cte`, que é responsável por mapear esses modelos nos documentos
fiscais do Odoo (`l10n_br_fiscal.document`), adicionar as regras de negócio e
realizar a comunicação com os web services da SEFAZ. Essa arquitetura
desacoplada segue o mesmo padrão de sucesso já utilizado pelos módulos
`l10n_br_nfe_spec` e `l10n_br_nfe`.

## Estrutura por Modal de Transporte

Para garantir a conformidade com as particularidades de cada operação, o
módulo implementa modelos de dados específicos para todos os modais de
transporte previstos na legislação:

- Rodoviário (`cte.40.rodo`): Contempla informações essenciais como o RNTRC e
  as Ordens de Coleta associadas.
- Aéreo (`cte.40.aereo`): Inclui campos para o número da minuta, o número
  operacional do conhecimento aéreo (IATA) e detalhes sobre a natureza e
  periculosidade da carga.
- Aquaviário (`cte.40.aquav`): Aborda dados como o valor do AFRMM, a
  identificação do navio, informações de balsas e o detalhamento de
  contêineres.
- Ferroviário (`cte.40.ferrov`): Permite detalhar o tipo de tráfego (próprio,
  mútuo, etc.) e as ferrovias envolvidas na operação.
- Dutoviário (`cte.40.duto`): Contém campos para o valor da tarifa, as datas
  de início e fim do serviço e as características do duto.
- Multimodal (`cte.40.multimodal`): Estruturado para gerenciar o Certificado
  do Operador de Transporte Multimodal (COTM) e as informações de seguro
  associadas.

## Geração de Código Automatizada

A principal característica deste módulo é que 100% dos seus modelos de dados
Odoo são gerados automaticamente a partir dos esquemas XSD oficiais,
publicados pelo Portal do CT-e. Essa geração pelo `xsdata-odoo` garante máxima
fidelidade aos leiautes fiscais e agilidade na atualização para novas versões.

Embora os esquemas XSD oficiais do CT-e sejam publicados e mantidos no Portal
da SEFAZ, a arquitetura deste projeto se apoia na biblioteca `nfelib` para a
tarefa de serialização dos dados em XML. Para facilitar o processo de
desenvolvimento e garantir a consistência, a própria `nfelib` armazena em seu
repositório uma cópia atualizada desses esquemas oficiais.

Portanto, a prática recomendada para (re)gerar os modelos deste módulo é
utilizar um clone local do repositório da nfelib como fonte para os arquivos
de esquema (.xsd), direcionando o comando do `xsdata-odoo` para o diretório
correspondente.

Links:

- [GitHub - akretion/xsdata-odoo](https://github.com/akretion/xsdata-odoo)
- [GitHub - akretion/nfelib](https://github.com/akretion/nfelib)

O comando utilizado para gerar os modelos da versão 4.0 do CT-e foi:

```bash
git clone https://github.com/akretion/nfelib
cd nfelib
export XSDATA_SCHEMA=cte
export XSDATA_VERSION=40
export XSDATA_SKIP="^ICMS\d+|^ICMSSN+|ICMSOutraUF|ICMSUFFim|INFESPECIE_TPESPECIE"
export XSDATA_LANG="portuguese"

xsdata generate nfelib/cte/schemas/v4_0 \
  --package nfelib.cte.odoo.v4_0 \
  --output=odoo
```

## Prefixo dos campos e versão

Com mais de 1000 campos fiscais apenas no CT-e, com uma meia dúzia de
documentos fiscais complexos, com 3000 módulos OCA, existiria um risco real de
conflito com os nomes de campos vindo dos esquemas. Além disso, temos várias
versões do CT-e, a 3.0, a 4.0...

Nisso foi decidido que cada campo tem um prefixo composto do nome do schema e
de alguns dígitos da versão do esquema. No caso cte40_. A escolha de 2 dígitos
permite que uma atualização menor do esquema use os mesmos campos (e dados no
banco então) e que um simples update Odoo (--update=...) consiga resolver a
migração. Enquanto que para uma mudança maior como de 3.0 para 4.0, seria
assumido de usar novos campos e novas tabelas (para os objetos não Odoo) e que
a lib nfelib iria trabalhar com os campos da versão maior do documento fiscal
considerado.
