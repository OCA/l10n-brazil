Instale este módulo só como dependência de `l10n_br_dere`.

Os nomes de campo usam o prefixo `dere12_` (leiaute 1.2.x). Um leiaute
major posterior introduziria um prefixo novo, na mesma convenção de
`l10n_br_nfe_spec`.

Os mixins da Onda 1 em `models/v1_2/` são os abstracts planos
curados usados por `l10n_br_dere` (`dere.12.infoconta`,
`dere.12.balanceteconta`, `dere.12.evtretornostabela`,
`dere.12.gtotalcodtrib`, `dere.12.detbc`, …). Não os substitua por um
dump cru do `xsdata-odoo` até a raiz oficial `DeRE` ser namespaced por
evento (veja o ROADMAP).

`validate()` confere os eventos de saída contra `EVENT_SCHEMA`.
`validate_return()` escolhe o XSD pelo namespace do retorno
(`RETURN_SCHEMA`), para o XML D-9xxx ser validado sem adivinhar o
tipo do evento.
