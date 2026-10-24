Este módulo é a fundação de dados da **EFD-Reinf** (Escrituração Fiscal Digital
de Retenções e Outras Informações Fiscais) no Odoo: uma biblioteca de modelos
abstratos (mixins) gerada automaticamente a partir dos esquemas XSD oficiais
publicados no portal do SPED.

Ele não transmite nada e não implementa regra de negócio: quem faz a apuração,
a montagem dos eventos e a comunicação com os web services da Receita é o
módulo `l10n_br_reinf`. Essa separação entre estrutura de dados gerada e lógica
de emissão é a mesma já usada na NF-e (`l10n_br_nfe_spec`), no CT-e e no MDF-e.

## Leiaute coberto

Leiaute **2.1.2b** (pacote de XSD "EFD-Reinf v2.1.2 - CNPJ Alfanumérico",
que incorpora a NT 03/2026 do CNPJ alfanumérico, com os padrões `[0-9A-Z]{14}`
nas inscrições). Um arquivo de mixins por evento:

- **R-1000** (informações do contribuinte), **R-1050** (tabela de entidades
  ligadas) e **R-1070** (tabela de processos administrativos e judiciais);
- **R-2010/R-2020** (retenção previdenciária de serviços tomados e prestados),
  **R-2030/R-2040** (recursos de associação desportiva), **R-2050/R-2055**
  (produção rural), **R-2060** (CPRB), **R-2098/R-2099** (reabertura e
  fechamento da série R-2000);
- **R-4010/R-4020/R-4040/R-4080** (pagamentos e retenções na fonte a pessoa
  física, pessoa jurídica, beneficiário não identificado e retenção no
  recebimento) e **R-4099** (fechamento e reabertura da série R-4000);
- **R-9000** (exclusão de evento);
- **R-9001/R-9005/R-9011/R-9015** (totalizadores devolvidos pela Receita, que
  são a fonte oficial do valor por código de receita que alimenta a DCTFWeb).

## Uma diferença importante em relação à NF-e

A NF-e tem um leiaute único (`leiauteNFe_v4.00.xsd`). A EFD-Reinf **não**: cada
evento é um XSD, um namespace XML e um módulo Python próprios. Por isso o mixin
`spec.mixin.reinf` traz apenas um par `_reinf21_odoo_module` /
`_reinf21_binding_module` como valor de partida, e **cada modelo concreto do
`l10n_br_reinf` redeclara esse par com o módulo do seu evento**.

Os esquemas do envelope do lote assíncrono (`envioLoteEventosAssincrono`
v1.00.00 e `retornoLoteEventosAssincrono` v1.00.00) e da consulta de recibos
(`retornoRecibosChaveEvento` v1.05.01) são outras famílias de esquema, com
versões próprias, e não entram neste módulo: ver `readme/ROADMAP.md`.

## Prefixo dos campos

Todos os campos gerados têm o prefixo `reinf21_` (nome do esquema mais dois
dígitos da versão) e todos os modelos ficam no namespace `reinf.21.*`. Os dois
dígitos permitem que uma revisão menor do leiaute reaproveite os mesmos campos
(e os mesmos dados no banco), resolvendo a migração com um simples `--update`;
uma mudança maior de versão ganharia campos e tabelas novos. A convenção é a
mesma do `nfe40_` e do `cte40_`.

## Geração do código

100% dos modelos deste módulo são gerados pelo
[xsdata-odoo](https://github.com/akretion/xsdata-odoo) a partir dos XSD
oficiais, que ficam versionados na
[nfelib](https://github.com/akretion/nfelib) junto com os bindings de
serialização. Para regerar:

```bash
git clone https://github.com/akretion/nfelib
cd nfelib
export XSDATA_SCHEMA=reinf
export XSDATA_VERSION=21
export XSDATA_LANG="portuguese"

xsdata generate nfelib/reinf/schemas/v2_01_02 \
  --package nfelib.reinf.odoo.v2_01_02 \
  --output=odoo

cp nfelib/reinf/odoo/v2_01_02/*.py \
  <caminho_do_odoo>/l10n_br_reinf_spec/models/v2_01_02/
```

Os arquivos das famílias de esquema do envelope e da consulta de recibos são
descartados nessa cópia (ver `readme/ROADMAP.md`), e o
`models/v2_01_02/__init__.py` é mantido à mão.
