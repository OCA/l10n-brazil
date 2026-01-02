Este módulo contém algumas abstrações utilizadas pelos módulos de SPED

Ele não faz nada sozinho, mas serve dentro dos 4 módulos:

- l10n_br_sped_ecd
- l10n_br_sped_efd_icms_ipi
- l10n_br_sped_efd_pis_cofins
- l10n_br_sped_ecf

Em especial, cada registro dos módulos de SPED herda do objeto abstrato
l10n_br_sped.mixin que conta com visões automáticas e metodos para
importar ou escrever registros dos SPED de forma recursiva.

Para cada tipo de arquivo SPED, o registro de abertura 0000 herda também
do objeto abstrato l10n_br_sped.declaration que conta com métodos para
popular os registros do SPED a partir das transações do Odoo entre as datas
DT_INI e DT_FIN e permite assim gerir os arquivos do SPED.

Para gerir o SPED, basta criar uma declaração do SPED no menu
apropriado. Depois clicar em Puxar os Dados do Odoo. Isso vai percorrer a
arvore dos registros do SPED e para cada registro vai usar `_odoo_domain`
ou `_odoo_query` para ver se tem records Odoo para mapear. Caso tiver vai
chamar o método `_map_from_odoo` do registro. Depois vai repetir a
operação com os registros filhos. Na declaração é possível escolher se você
quer um único arquivo SPED ou se você quer quebrar o arquivo bloco por
bloco.

Em cada módulo de SPED, existe 2 arquivos principais:

- um arquivo com o número do leiaute que contém **os modelos abstratos
  de todos os registros do SPED com todos os campos**. Este arquivo é gerido
  gerido pela ferramenta
  [spedextractor](https://github.com/akretion/sped-extractor) a partir dos pdf
  das especificações e **não deve ser editado manualmente**.
- um segundo arquivo que contém a **lista de todos registros
  concretos** que herdam desses primeiros modelos abstratos e contém
  assim todos os campos. Como o mixin de cada registro contém a versão
  do leiaute dentro do nome dele, temos uma forma de suportar
  várias versões dos leiautes. Esse arquivo dos registros concretos
  deve sim ser editado manualmente para completar os mappings. Para
  mapear um registro, deve se implementar o override desses 3 métodos:
  - `def _odoo_domain(self, parent_record, declaration):` deve
    retornar um domain que permite a seleção dos records Odoo a serem
    mapeados de acordo com o record parente e os dados da declaração
    (onde tem as datas e a empresa por exemplo). Para usar esse método
    `_odoo_domain`, deve se definir também o atributo `_odoo_model`
  - `def _odoo_query(self, parent_record, declaration): ` caso a
    seleção dos records a serem mapeados não pode ser obtida por um
    domain, pode ser implementado esse override para retornar a query
    SQL para selecionar um result set a mapear. Neste caso, o record
    do método `_map_from_odoo` é um result set do query Postgres. Se
    você não implementar nem `_odoo_domain` nem `_odoo_query` e
    implementar o método `_map_from_odoo`, o registro vai ter uma
    instância gerida para cada declaração. É o caso do registro I010
    da ECD por exemplo.
  - `_map_from_odoo(self, record, parent_record, declaration, index=0)`
    para facilitar, os overrides dos metodos `_map_from_odoo` de
    todos os registros, esse já vem geridos de forma comentada com
    todos os campos do registro. Assim basta descomentar or método e
    implementar como é mapeado cada campo a partir do record,
    parent_record e dos dados da declaração.
