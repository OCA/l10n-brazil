Os nomes de campo usam o prefixo `dere12_` (leiaute 1.2.x). Um leiaute
major posterior introduziria um prefixo novo, na mesma convenção de
`l10n_br_nfe_spec`.

Os mixins da Onda 1 em `models/v1_2/` saem do `xsdata-odoo` 1.2.2, um
XSD por vez. A raiz oficial ainda se chama `DeRE` em todo evento, então
cada arquivo recebe um sufixo no `_name` e no `comodel_name`
(`dere.12.d1101.infoconta`). O prefixo dos campos não muda. Não edite
campo, string nem `Many2one` desses arquivos: a próxima geração deve
mostrar só o que o esquema mudou.

```bash
export XSDATA_SCHEMA=dere
export XSDATA_VERSION=12
export XSDATA_LANG=portuguese
export XSDATA_HEADER=$'Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>\nLicense LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).'
export XSDATA_SCHEMA_NOTE="DeRE layout 1.2.0 / D-1011"
xsdata generate evtPGCC-v1_0_3.xsd --output=odoo
```

Troque o código do evento na nota. No arquivo gerado, substitua
`dere.12.` por `dere.12.d1011.` em `_name`, `comodel_name` e no primeiro
argumento de `One2many`.

`regTribSecund` (simpleType anônimo) e `ds:Signature` não saem do
gerador. O XML deles continua em `l10n_br_dere`. `dere.12.detbc` e
`dere.12.totaltributos`, em `flattened.py`, continuam à mão: o XSD
repete os mesmos nomes em grupos diferentes.

`validate()` confere os eventos de saída contra `EVENT_SCHEMA`.
`validate_return()` escolhe o XSD pelo namespace do retorno
(`RETURN_SCHEMA`), para o XML D-9xxx ser validado sem adivinhar o
tipo do evento.

`safe_fromstring()` lê o XML sem expandir entidades nem acessar a
rede. Os validadores já a usam; use-a também para ler qualquer
retorno do gateway.
